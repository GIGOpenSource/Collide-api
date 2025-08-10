"""
博主申请服务
"""
from typing import Optional, Dict
from sqlalchemy import select, insert, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BusinessException
from app.domains.users.models import BloggerApplication, User, UserRole, Role
from app.domains.users.schemas import BloggerApplicationInfo


class BloggerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def apply_for_blogger(self, user_id: int) -> BloggerApplicationInfo:
        """申请博主权限"""
        try:
            # 检查用户是否已经是博主
            is_blogger = await self._check_blogger_status(user_id)
            if is_blogger:
                raise BusinessException("您已经是博主，无需重复申请")
            
            # 检查是否已经申请过
            existing_application = await self.db.execute(
                select(BloggerApplication).where(BloggerApplication.user_id == user_id)
            )
            existing_application = existing_application.scalar_one_or_none()
            
            if existing_application:
                if existing_application.status == "PENDING":
                    raise BusinessException("您已有待审核的博主申请，请耐心等待")
                elif existing_application.status == "APPROVED":
                    raise BusinessException("您的博主申请已通过，无需重复申请")
                elif existing_application.status == "REJECTED":
                    # 如果被拒绝，可以重新申请
                    await self.db.execute(
                        update(BloggerApplication)
                        .where(BloggerApplication.id == existing_application.id)
                        .values(status="PENDING")
                    )
                    await self.db.commit()
                    await self.db.refresh(existing_application)
                    return BloggerApplicationInfo.model_validate(existing_application)
            
            # 创建新的申请
            application = BloggerApplication(user_id=user_id, status="PENDING")
            self.db.add(application)
            await self.db.commit()
            await self.db.refresh(application)
            
            return BloggerApplicationInfo.model_validate(application)
            
        except BusinessException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"申请博主权限失败: {str(e)}")

    async def get_application_status(self, user_id: int) -> BloggerApplicationInfo:
        """获取申请状态"""
        application = await self.db.execute(
            select(BloggerApplication).where(BloggerApplication.user_id == user_id)
        )
        application = application.scalar_one_or_none()
        
        if not application:
            raise BusinessException("您还没有申请博主权限")
        
        return BloggerApplicationInfo.model_validate(application)

    async def check_blogger_status(self, user_id: int) -> Dict:
        """检查博主状态"""
        # 检查是否已经是博主
        is_blogger = await self._check_blogger_status(user_id)
        
        # 获取申请状态
        application = await self.db.execute(
            select(BloggerApplication).where(BloggerApplication.user_id == user_id)
        )
        application = application.scalar_one_or_none()
        
        application_status = None
        if application:
            application_status = application.status
        
        # 判断是否可以申请
        can_apply = not is_blogger and (not application or application.status == "REJECTED")
        
        return {
            "is_blogger": is_blogger,
            "application_status": application_status,
            "can_apply": can_apply
        }

    async def _check_blogger_status(self, user_id: int) -> bool:
        """检查用户是否已经是博主"""
        stmt = (
            select(Role.name)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        roles = [row[0] for row in result.all()]
        return "blogger" in roles

    async def approve_blogger_application(self, application_id: int, admin_user_id: int) -> BloggerApplicationInfo:
        """管理员批准博主申请"""
        try:
            # 获取申请
            application = await self.db.execute(
                select(BloggerApplication).where(BloggerApplication.id == application_id)
            )
            application = application.scalar_one_or_none()
            
            if not application:
                raise BusinessException("申请不存在")
            
            if application.status != "PENDING":
                raise BusinessException("申请状态不是待审核")
            
            # 更新申请状态
            await self.db.execute(
                update(BloggerApplication)
                .where(BloggerApplication.id == application_id)
                .values(status="APPROVED")
            )
            
            # 获取博主角色ID
            blogger_role = await self.db.execute(
                select(Role).where(Role.name == "blogger")
            )
            blogger_role = blogger_role.scalar_one_or_none()
            
            if not blogger_role:
                raise BusinessException("博主角色不存在，请联系管理员")
            
            # 检查是否已经有博主角色
            existing_role = await self.db.execute(
                select(UserRole).where(
                    and_(UserRole.user_id == application.user_id, UserRole.role_id == blogger_role.id)
                )
            )
            existing_role = existing_role.scalar_one_or_none()
            
            if not existing_role:
                # 添加博主角色
                user_role = UserRole(
                    user_id=application.user_id,
                    role_id=blogger_role.id
                )
                self.db.add(user_role)
            
            await self.db.commit()
            await self.db.refresh(application)
            
            return BloggerApplicationInfo.model_validate(application)
            
        except BusinessException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"批准博主申请失败: {str(e)}")

    async def reject_blogger_application(self, application_id: int, admin_user_id: int, reason: Optional[str] = None) -> BloggerApplicationInfo:
        """管理员拒绝博主申请"""
        try:
            # 获取申请
            application = await self.db.execute(
                select(BloggerApplication).where(BloggerApplication.id == application_id)
            )
            application = application.scalar_one_or_none()
            
            if not application:
                raise BusinessException("申请不存在")
            
            if application.status != "PENDING":
                raise BusinessException("申请状态不是待审核")
            
            # 更新申请状态
            await self.db.execute(
                update(BloggerApplication)
                .where(BloggerApplication.id == application_id)
                .values(status="REJECTED")
            )
            
            await self.db.commit()
            await self.db.refresh(application)
            
            return BloggerApplicationInfo.model_validate(application)
            
        except BusinessException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"拒绝博主申请失败: {str(e)}")

    async def get_pending_applications(self, limit: int = 20) -> list[BloggerApplicationInfo]:
        """获取待审核的申请列表"""
        applications = await self.db.execute(
            select(BloggerApplication)
            .where(BloggerApplication.status == "PENDING")
            .order_by(BloggerApplication.create_time.asc())
            .limit(limit)
        )
        return [BloggerApplicationInfo.model_validate(app) for app in applications.scalars().all()] 