"""
内容模块异步业务逻辑服务
"""
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import selectinload

from app.domains.content.models import Content, ContentChapter, ContentPayment, UserContentPurchase
from app.domains.content.schemas import (
    ContentCreate, ContentUpdate, ContentInfo, ContentQueryParams,
    ChapterCreate, ChapterUpdate, ChapterInfo, ChapterListItem,
    ContentPaymentCreate, ContentPaymentUpdate, ContentPaymentInfo,
    UserContentPurchaseCreate, UserContentPurchaseInfo,
    PublishContentRequest, ContentStatsUpdate, ScoreContentRequest
)
from app.common.exceptions import BusinessException, ContentNotFoundError, ChapterNotFoundError
from app.common.pagination import PaginationParams, PaginationResult


class ContentAsyncService:
    """内容异步服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ================ 内容管理 ================

    async def create_content(self, content_data: ContentCreate, author_id: int, author_nickname: str = None, author_avatar: str = None) -> ContentInfo:
        """创建内容"""
        try:
            # 创建内容对象
            content = Content(
                title=content_data.title,
                description=content_data.description,
                content_type=content_data.content_type,
                content_data=content_data.content_data,
                cover_url=content_data.cover_url,
                tags=content_data.tags,
                category_id=content_data.category_id,
                category_name=content_data.category_name,
                author_id=author_id,
                author_nickname=author_nickname,
                author_avatar=author_avatar,
                status="DRAFT",
                review_status="PENDING"
            )
            
            self.db.add(content)
            await self.db.commit()
            await self.db.refresh(content)
            
            return ContentInfo.model_validate(content)
            
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"创建内容失败: {str(e)}")

    async def get_content_by_id(self, content_id: int, user_id: int = None) -> ContentInfo:
        """根据ID获取内容详情"""
        stmt = select(Content).where(Content.id == content_id)
        result = await self.db.execute(stmt)
        content = result.scalar_one_or_none()
        
        if not content:
            raise ContentNotFoundError()
        
        # 如果提供了用户ID，增加浏览量
        if user_id:
            await self.increment_content_stats(content_id, "view")
        
        return ContentInfo.model_validate(content)

    async def update_content(self, content_id: int, content_data: ContentUpdate, author_id: int) -> ContentInfo:
        """更新内容"""
        try:
            # 检查内容是否存在且属于当前用户
            stmt = select(Content).where(and_(Content.id == content_id, Content.author_id == author_id))
            result = await self.db.execute(stmt)
            content = result.scalar_one_or_none()
            
            if not content:
                raise ContentNotFoundError("内容不存在或无权限修改")
            
            # 更新字段
            update_data = content_data.model_dump(exclude_unset=True)
            if update_data:
                stmt = update(Content).where(Content.id == content_id).values(**update_data)
                await self.db.execute(stmt)
                await self.db.commit()
                
                # 重新获取更新后的内容
                await self.db.refresh(content)
            
            return ContentInfo.model_validate(content)
            
        except ContentNotFoundError:
            raise
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"更新内容失败: {str(e)}")

    async def delete_content(self, content_id: int, author_id: int) -> bool:
        """删除内容"""
        try:
            # 检查内容是否存在且属于当前用户
            stmt = select(Content).where(and_(Content.id == content_id, Content.author_id == author_id))
            result = await self.db.execute(stmt)
            content = result.scalar_one_or_none()
            
            if not content:
                raise ContentNotFoundError("内容不存在或无权限删除")
            
            # 删除相关章节
            await self.db.execute(delete(ContentChapter).where(ContentChapter.content_id == content_id))
            
            # 删除付费配置
            await self.db.execute(delete(ContentPayment).where(ContentPayment.content_id == content_id))
            
            # 删除内容
            await self.db.execute(delete(Content).where(Content.id == content_id))
            
            await self.db.commit()
            return True
            
        except ContentNotFoundError:
            raise
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"删除内容失败: {str(e)}")

    async def publish_content(self, content_id: int, author_id: int, publish_request: PublishContentRequest) -> ContentInfo:
        """发布内容"""
        try:
            # 检查内容是否存在且属于当前用户
            stmt = select(Content).where(and_(Content.id == content_id, Content.author_id == author_id))
            result = await self.db.execute(stmt)
            content = result.scalar_one_or_none()
            
            if not content:
                raise ContentNotFoundError("内容不存在或无权限发布")
            
            if content.status == "PUBLISHED":
                raise BusinessException("内容已发布")
            
            # 更新发布状态
            publish_time = publish_request.publish_time or datetime.utcnow()
            stmt = update(Content).where(Content.id == content_id).values(
                status="PUBLISHED",
                publish_time=publish_time,
                review_status="APPROVED"  # 自动通过审核
            )
            await self.db.execute(stmt)
            await self.db.commit()
            
            # 重新获取更新后的内容
            await self.db.refresh(content)
            return ContentInfo.model_validate(content)
            
        except (ContentNotFoundError, BusinessException):
            raise
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"发布内容失败: {str(e)}")

    async def get_content_list(self, query_params: ContentQueryParams, pagination: PaginationParams) -> PaginationResult[ContentInfo]:
        """获取内容列表"""
        try:
            # 构建查询条件
            conditions = []
            
            # 基础筛选条件
            if query_params.content_type:
                conditions.append(Content.content_type == query_params.content_type)
            if query_params.category_id:
                conditions.append(Content.category_id == query_params.category_id)
            if query_params.author_id:
                conditions.append(Content.author_id == query_params.author_id)
            if query_params.status:
                conditions.append(Content.status == query_params.status)
            if query_params.review_status:
                conditions.append(Content.review_status == query_params.review_status)
                
            # 关键词搜索
            if query_params.keyword:
                keyword_condition = or_(
                    Content.title.contains(query_params.keyword),
                    Content.description.contains(query_params.keyword),
                    Content.tags.contains(query_params.keyword),
                    Content.author_nickname.contains(query_params.keyword)
                )
                conditions.append(keyword_condition)
            
            # 统计数据筛选
            if query_params.min_view_count is not None:
                conditions.append(Content.view_count >= query_params.min_view_count)
            if query_params.max_view_count is not None:
                conditions.append(Content.view_count <= query_params.max_view_count)
            if query_params.min_like_count is not None:
                conditions.append(Content.like_count >= query_params.min_like_count)
            if query_params.max_like_count is not None:
                conditions.append(Content.like_count <= query_params.max_like_count)
            if query_params.min_favorite_count is not None:
                conditions.append(Content.favorite_count >= query_params.min_favorite_count)
            if query_params.max_favorite_count is not None:
                conditions.append(Content.favorite_count <= query_params.max_favorite_count)
            if query_params.min_comment_count is not None:
                conditions.append(Content.comment_count >= query_params.min_comment_count)
            if query_params.max_comment_count is not None:
                conditions.append(Content.comment_count <= query_params.max_comment_count)
            
            # 评分筛选（需要计算平均分）
            if query_params.min_score is not None:
                # 只查询有评分的内容，且平均分 >= 最低分
                conditions.append(Content.score_count > 0)
                conditions.append((Content.score_total / Content.score_count) >= query_params.min_score)
            if query_params.max_score is not None:
                # 只查询有评分的内容，且平均分 <= 最高分
                conditions.append(Content.score_count > 0)
                conditions.append((Content.score_total / Content.score_count) <= query_params.max_score)
            
            # 时间筛选
            if query_params.publish_date_start:
                try:
                    start_date = datetime.strptime(query_params.publish_date_start, "%Y-%m-%d")
                    conditions.append(Content.publish_time >= start_date)
                except ValueError:
                    pass
            if query_params.publish_date_end:
                try:
                    end_date = datetime.strptime(query_params.publish_date_end, "%Y-%m-%d")
                    # 包含整个结束日期
                    end_date = end_date.replace(hour=23, minute=59, second=59)
                    conditions.append(Content.publish_time <= end_date)
                except ValueError:
                    pass
            if query_params.create_date_start:
                try:
                    start_date = datetime.strptime(query_params.create_date_start, "%Y-%m-%d")
                    conditions.append(Content.create_time >= start_date)
                except ValueError:
                    pass
            if query_params.create_date_end:
                try:
                    end_date = datetime.strptime(query_params.create_date_end, "%Y-%m-%d")
                    end_date = end_date.replace(hour=23, minute=59, second=59)
                    conditions.append(Content.create_time <= end_date)
                except ValueError:
                    pass
            
            # 标签筛选
            if query_params.tags:
                tag_list = [tag.strip() for tag in query_params.tags.split(",") if tag.strip()]
                if tag_list:
                    tag_conditions = [Content.tags.contains(tag) for tag in tag_list]
                    # 使用 OR 条件，只要包含任意一个标签就符合条件
                    conditions.append(or_(*tag_conditions))
            
            # 构建主查询
            stmt = select(Content)
            
            # 付费筛选需要关联 ContentPayment 表
            if query_params.is_free is not None or query_params.is_vip_free is not None:
                from app.domains.content.models import ContentPayment
                
                if query_params.is_free is True:
                    # 免费内容：没有付费配置或付费类型为 FREE
                    free_condition = or_(
                        ~select(ContentPayment.id).where(ContentPayment.content_id == Content.id).exists(),
                        select(ContentPayment.payment_type).where(
                            and_(ContentPayment.content_id == Content.id, ContentPayment.payment_type == "FREE")
                        ).exists()
                    )
                    conditions.append(free_condition)
                elif query_params.is_free is False:
                    # 付费内容：有付费配置且付费类型不为 FREE
                    paid_condition = select(ContentPayment.id).where(
                        and_(ContentPayment.content_id == Content.id, ContentPayment.payment_type != "FREE")
                    ).exists()
                    conditions.append(paid_condition)
                
                if query_params.is_vip_free is True:
                    # VIP免费
                    vip_free_condition = select(ContentPayment.id).where(
                        and_(ContentPayment.content_id == Content.id, ContentPayment.vip_free == 1)
                    ).exists()
                    conditions.append(vip_free_condition)
                elif query_params.is_vip_free is False:
                    # 非VIP免费
                    vip_not_free_condition = or_(
                        ~select(ContentPayment.id).where(ContentPayment.content_id == Content.id).exists(),
                        select(ContentPayment.id).where(
                            and_(ContentPayment.content_id == Content.id, ContentPayment.vip_free == 0)
                        ).exists()
                    )
                    conditions.append(vip_not_free_condition)
            
            # 应用所有筛选条件
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            # 排序
            sort_column = Content.create_time  # 默认排序
            if query_params.sort_by == "create_time":
                sort_column = Content.create_time
            elif query_params.sort_by == "update_time":
                sort_column = Content.update_time
            elif query_params.sort_by == "publish_time":
                sort_column = Content.publish_time
            elif query_params.sort_by == "view_count":
                sort_column = Content.view_count
            elif query_params.sort_by == "like_count":
                sort_column = Content.like_count
            elif query_params.sort_by == "favorite_count":
                sort_column = Content.favorite_count
            elif query_params.sort_by == "comment_count":
                sort_column = Content.comment_count
            elif query_params.sort_by == "score":
                # 按平均评分排序
                sort_column = func.coalesce(Content.score_total / func.nullif(Content.score_count, 0), 0)
            
            if query_params.sort_order == "asc":
                stmt = stmt.order_by(sort_column.asc())
            else:
                stmt = stmt.order_by(sort_column.desc())
            
            # 添加二级排序以保证结果一致性
            if query_params.sort_by != "create_time":
                stmt = stmt.order_by(Content.create_time.desc())
            
            # 分页
            total_stmt = select(func.count()).select_from(stmt.subquery())
            total_result = await self.db.execute(total_stmt)
            total = total_result.scalar()
            
            stmt = stmt.offset(pagination.offset).limit(pagination.limit)
            result = await self.db.execute(stmt)
            contents = result.scalars().all()
            
            content_list = [ContentInfo.model_validate(content) for content in contents]
            
            return PaginationResult(
                items=content_list,
                total=total,
                page=pagination.page,
                size=pagination.size,
                pages=(total + pagination.size - 1) // pagination.size
            )
            
        except Exception as e:
            raise BusinessException(f"获取内容列表失败: {str(e)}")

    async def increment_content_stats(self, content_id: int, stats_type: str, increment: int = 1) -> bool:
        """增加内容统计数据"""
        try:
            if stats_type == "view":
                column = Content.view_count
            elif stats_type == "like":
                column = Content.like_count
            elif stats_type == "comment":
                column = Content.comment_count
            elif stats_type == "share":
                column = Content.share_count
            elif stats_type == "favorite":
                column = Content.favorite_count
            else:
                raise BusinessException(f"不支持的统计类型: {stats_type}")
            
            stmt = update(Content).where(Content.id == content_id).values({column: column + increment})
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            return result.rowcount > 0
            
        except BusinessException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"更新统计数据失败: {str(e)}")

    async def score_content(self, content_id: int, user_id: int, score_request: ScoreContentRequest) -> bool:
        """为内容评分"""
        try:
            # 检查内容是否存在
            stmt = select(Content).where(Content.id == content_id)
            result = await self.db.execute(stmt)
            content = result.scalar_one_or_none()
            
            if not content:
                raise ContentNotFoundError()
            
            # TODO: 这里应该检查用户是否已经评过分，如果评过分则更新，否则新增
            # 为了简化，这里直接增加评分统计
            
            # 更新评分统计
            stmt = update(Content).where(Content.id == content_id).values(
                score_count=Content.score_count + 1,
                score_total=Content.score_total + score_request.score
            )
            await self.db.execute(stmt)
            await self.db.commit()
            
            return True
            
        except ContentNotFoundError:
            raise
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"评分失败: {str(e)}")

    # ================ 章节管理 ================

    async def create_chapter(self, chapter_data: ChapterCreate, author_id: int) -> ChapterInfo:
        """创建章节"""
        try:
            # 检查内容是否存在且属于当前用户
            stmt = select(Content).where(and_(Content.id == chapter_data.content_id, Content.author_id == author_id))
            result = await self.db.execute(stmt)
            content = result.scalar_one_or_none()
            
            if not content:
                raise ContentNotFoundError("内容不存在或无权限添加章节")
            
            # 检查章节号是否已存在
            stmt = select(ContentChapter).where(
                and_(ContentChapter.content_id == chapter_data.content_id, 
                     ContentChapter.chapter_num == chapter_data.chapter_num)
            )
            result = await self.db.execute(stmt)
            existing_chapter = result.scalar_one_or_none()
            
            if existing_chapter:
                raise BusinessException("章节号已存在")
            
            # 创建章节
            chapter = ContentChapter(
                content_id=chapter_data.content_id,
                chapter_num=chapter_data.chapter_num,
                title=chapter_data.title,
                content=chapter_data.content,
                word_count=chapter_data.word_count,
                status="DRAFT"
            )
            
            self.db.add(chapter)
            await self.db.commit()
            await self.db.refresh(chapter)
            
            return ChapterInfo.model_validate(chapter)
            
        except (ContentNotFoundError, BusinessException):
            raise
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"创建章节失败: {str(e)}")

    async def get_chapter_by_id(self, chapter_id: int, user_id: int = None) -> ChapterInfo:
        """根据ID获取章节详情"""
        stmt = select(ContentChapter).where(ContentChapter.id == chapter_id)
        result = await self.db.execute(stmt)
        chapter = result.scalar_one_or_none()
        
        if not chapter:
            raise ChapterNotFoundError()
        
        # TODO: 检查用户是否有权限访问该章节（购买检查等）
        
        return ChapterInfo.model_validate(chapter)

    async def get_content_chapters(self, content_id: int, user_id: int = None) -> List[ChapterListItem]:
        """获取内容的章节列表"""
        stmt = select(ContentChapter).where(ContentChapter.content_id == content_id).order_by(ContentChapter.chapter_num)
        result = await self.db.execute(stmt)
        chapters = result.scalars().all()
        
        # TODO: 根据用户购买情况过滤章节
        
        return [ChapterListItem.model_validate(chapter) for chapter in chapters]

    async def update_chapter(self, chapter_id: int, chapter_data: ChapterUpdate, author_id: int) -> ChapterInfo:
        """更新章节"""
        try:
            # 检查章节是否存在且用户有权限修改
            stmt = select(ContentChapter).join(Content).where(
                and_(ContentChapter.id == chapter_id, Content.author_id == author_id)
            )
            result = await self.db.execute(stmt)
            chapter = result.scalar_one_or_none()
            
            if not chapter:
                raise ChapterNotFoundError("章节不存在或无权限修改")
            
            # 更新字段
            update_data = chapter_data.model_dump(exclude_unset=True)
            if update_data:
                stmt = update(ContentChapter).where(ContentChapter.id == chapter_id).values(**update_data)
                await self.db.execute(stmt)
                await self.db.commit()
                
                # 重新获取更新后的章节
                await self.db.refresh(chapter)
            
            return ChapterInfo.model_validate(chapter)
            
        except ChapterNotFoundError:
            raise
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"更新章节失败: {str(e)}")

    async def delete_chapter(self, chapter_id: int, author_id: int) -> bool:
        """删除章节"""
        try:
            # 检查章节是否存在且用户有权限删除
            stmt = select(ContentChapter).join(Content).where(
                and_(ContentChapter.id == chapter_id, Content.author_id == author_id)
            )
            result = await self.db.execute(stmt)
            chapter = result.scalar_one_or_none()
            
            if not chapter:
                raise ChapterNotFoundError("章节不存在或无权限删除")
            
            # 删除章节
            await self.db.execute(delete(ContentChapter).where(ContentChapter.id == chapter_id))
            await self.db.commit()
            
            return True
            
        except ChapterNotFoundError:
            raise
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"删除章节失败: {str(e)}")

    # ================ 付费配置管理 ================

    async def create_content_payment(self, payment_data: ContentPaymentCreate, author_id: int) -> ContentPaymentInfo:
        """创建内容付费配置"""
        try:
            # 检查内容是否存在且属于当前用户
            stmt = select(Content).where(and_(Content.id == payment_data.content_id, Content.author_id == author_id))
            result = await self.db.execute(stmt)
            content = result.scalar_one_or_none()
            
            if not content:
                raise ContentNotFoundError("内容不存在或无权限配置付费")
            
            # 检查是否已有付费配置
            stmt = select(ContentPayment).where(ContentPayment.content_id == payment_data.content_id)
            result = await self.db.execute(stmt)
            existing_payment = result.scalar_one_or_none()
            
            if existing_payment:
                raise BusinessException("该内容已有付费配置")
            
            # 创建付费配置
            payment = ContentPayment(**payment_data.model_dump())
            
            self.db.add(payment)
            await self.db.commit()
            await self.db.refresh(payment)
            
            return ContentPaymentInfo.model_validate(payment)
            
        except (ContentNotFoundError, BusinessException):
            raise
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"创建付费配置失败: {str(e)}")

    async def get_content_payment(self, content_id: int) -> Optional[ContentPaymentInfo]:
        """获取内容付费配置"""
        stmt = select(ContentPayment).where(ContentPayment.content_id == content_id)
        result = await self.db.execute(stmt)
        payment = result.scalar_one_or_none()
        
        if payment:
            return ContentPaymentInfo.model_validate(payment)
        return None

    # ================ 购买记录管理 ================

    async def create_purchase_record(self, purchase_data: UserContentPurchaseCreate, user_id: int) -> UserContentPurchaseInfo:
        """创建购买记录"""
        try:
            # 获取内容信息
            stmt = select(Content).where(Content.id == purchase_data.content_id)
            result = await self.db.execute(stmt)
            content = result.scalar_one_or_none()
            
            if not content:
                raise ContentNotFoundError()
            
            # 检查是否已购买
            stmt = select(UserContentPurchase).where(
                and_(UserContentPurchase.user_id == user_id, 
                     UserContentPurchase.content_id == purchase_data.content_id,
                     UserContentPurchase.status == "ACTIVE")
            )
            result = await self.db.execute(stmt)
            existing_purchase = result.scalar_one_or_none()
            
            if existing_purchase:
                raise BusinessException("已购买该内容")
            
            # 创建购买记录
            purchase = UserContentPurchase(
                user_id=user_id,
                content_id=purchase_data.content_id,
                content_title=content.title,
                content_type=content.content_type,
                content_cover_url=content.cover_url,
                author_id=content.author_id,
                author_nickname=content.author_nickname,
                order_id=purchase_data.order_id,
                order_no=purchase_data.order_no,
                coin_amount=purchase_data.coin_amount,
                original_price=purchase_data.original_price,
                discount_amount=purchase_data.discount_amount,
                status="ACTIVE"
            )
            
            self.db.add(purchase)
            await self.db.commit()
            await self.db.refresh(purchase)
            
            return UserContentPurchaseInfo.model_validate(purchase)
            
        except (ContentNotFoundError, BusinessException):
            raise
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"创建购买记录失败: {str(e)}")

    async def check_user_purchase(self, user_id: int, content_id: int) -> Optional[UserContentPurchaseInfo]:
        """检查用户是否购买了内容"""
        stmt = select(UserContentPurchase).where(
            and_(UserContentPurchase.user_id == user_id, 
                 UserContentPurchase.content_id == content_id,
                 UserContentPurchase.status == "ACTIVE")
        )
        result = await self.db.execute(stmt)
        purchase = result.scalar_one_or_none()
        
        if purchase:
            return UserContentPurchaseInfo.model_validate(purchase)
        return None

    async def get_user_purchases(self, user_id: int, pagination: PaginationParams) -> PaginationResult[UserContentPurchaseInfo]:
        """获取用户购买记录"""
        try:
            # 构建查询
            stmt = select(UserContentPurchase).where(UserContentPurchase.user_id == user_id)
            stmt = stmt.order_by(UserContentPurchase.purchase_time.desc())
            
            # 分页
            total_stmt = select(func.count()).select_from(stmt.subquery())
            total_result = await self.db.execute(total_stmt)
            total = total_result.scalar()
            
            stmt = stmt.offset(pagination.offset).limit(pagination.limit)
            result = await self.db.execute(stmt)
            purchases = result.scalars().all()
            
            purchase_list = [UserContentPurchaseInfo.model_validate(purchase) for purchase in purchases]
            
            return PaginationResult(
                items=purchase_list,
                total=total,
                page=pagination.page,
                size=pagination.size,
                pages=(total + pagination.size - 1) // pagination.size
            )
            
        except Exception as e:
            raise BusinessException(f"获取购买记录失败: {str(e)}")
