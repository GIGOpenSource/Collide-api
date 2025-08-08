"""
内容模块异步服务层 - 增强版
添加缓存和原子性支持
"""
from typing import Optional, List, Dict
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, delete, and_, or_, func

from app.domains.content.models import Content, Chapter, ContentPayment, UserContentPurchase
from app.domains.content.schemas import (
    ContentCreate, ContentUpdate, ContentInfo, ContentQueryParams,
    ChapterCreate, ChapterUpdate, ChapterInfo, ChapterListItem,
    ContentPaymentCreate, ContentPaymentInfo,
    UserContentPurchaseCreate, UserContentPurchaseInfo,
    PublishContentRequest, ContentStatsUpdate, ScoreContentRequest
)
from app.common.pagination import PaginationParams, PaginationResult
from app.common.exceptions import BusinessException
from app.common.cache_service import cache_service
from app.common.atomic import atomic_transaction, atomic_lock, atomic_optimistic


class ContentAsyncService:
    """内容异步服务类 - 增强版"""

    def __init__(self, db: AsyncSession):
        self.db = db

    @atomic_transaction()
    async def create_content(self, content_data: ContentCreate, user_id: int) -> ContentInfo:
        """创建内容 - 带原子性事务"""
        content = Content(
            title=content_data.title,
            description=content_data.description,
            content_type=content_data.content_type,
            category_id=content_data.category_id,
            author_id=user_id,
            content=content_data.content,
            cover_url=content_data.cover_url,
            tags=content_data.tags,
            status="DRAFT",
            review_status="PENDING"
        )
        
        self.db.add(content)
        await self.db.commit()
        await self.db.refresh(content)

        # 清除相关缓存
        await cache_service.delete_pattern("content:*")
        await cache_service.delete_pattern("user:stats:*")

        return ContentInfo.model_validate(content)

    async def get_content_by_id(self, content_id: int, user_id: Optional[int] = None) -> ContentInfo:
        """获取内容详情 - 带缓存"""
        # 尝试从缓存获取
        cached_content = await cache_service.get_content_cache(content_id)
        if cached_content:
            return ContentInfo.model_validate(cached_content)

        # 缓存未命中，从数据库获取
        content = (await self.db.execute(select(Content).where(Content.id == content_id))).scalar_one_or_none()
        if not content:
            raise BusinessException("内容不存在")

        # 增加查看数
        await self.increment_content_stats(content_id, "view_count", 1)

        content_info = ContentInfo.model_validate(content)
        
        # 缓存内容信息
        await cache_service.set_content_cache(content_id, content_info.model_dump())
        
        return content_info

    @atomic_transaction()
    async def update_content(self, content_id: int, content_data: ContentUpdate, user_id: int) -> ContentInfo:
        """更新内容 - 带原子性事务"""
        content = (await self.db.execute(select(Content).where(Content.id == content_id))).scalar_one_or_none()
        if not content:
            raise BusinessException("内容不存在")

        if content.author_id != user_id:
            raise BusinessException("无权限修改此内容")

        # 更新字段
        update_data = {}
        if content_data.title is not None:
            update_data["title"] = content_data.title
        if content_data.description is not None:
            update_data["description"] = content_data.description
        if content_data.content_type is not None:
            update_data["content_type"] = content_data.content_type
        if content_data.category_id is not None:
            update_data["category_id"] = content_data.category_id
        if content_data.content is not None:
            update_data["content"] = content_data.content
        if content_data.cover_url is not None:
            update_data["cover_url"] = content_data.cover_url
        if content_data.tags is not None:
            update_data["tags"] = content_data.tags

        if update_data:
            await self.db.execute(update(Content).where(Content.id == content_id).values(**update_data))
            await self.db.commit()

        # 清除相关缓存
        await cache_service.delete_content_cache(content_id)
        await cache_service.delete_pattern("content:*")

        # 重新获取内容信息
        return await self.get_content_by_id(content_id, user_id)

    @atomic_transaction()
    async def delete_content(self, content_id: int, user_id: int) -> bool:
        """删除内容 - 带原子性事务"""
        content = (await self.db.execute(select(Content).where(Content.id == content_id))).scalar_one_or_none()
        if not content:
            raise BusinessException("内容不存在")

        if content.author_id != user_id:
            raise BusinessException("无权限删除此内容")

        await self.db.execute(delete(Content).where(Content.id == content_id))
        await self.db.commit()

        # 清除相关缓存
        await cache_service.delete_content_cache(content_id)
        await cache_service.delete_pattern("content:*")
        await cache_service.delete_pattern("user:stats:*")

        return True

    async def get_content_list(self, query_params: ContentQueryParams, pagination: PaginationParams) -> PaginationResult[ContentInfo]:
        """获取内容列表 - 带缓存"""
        # 生成缓存键
        cache_key = f"content:list:{hash(str(query_params.model_dump()) + str(pagination.model_dump()))}"
        
        # 尝试从缓存获取
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return PaginationResult.create(**cached_result)

        # 构建查询条件
        conditions = []
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
        if query_params.keyword:
            conditions.append(or_(
                Content.title.contains(query_params.keyword),
                Content.description.contains(query_params.keyword),
                Content.tags.contains(query_params.keyword)
            ))

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
        if query_params.min_score is not None:
            conditions.append(Content.score >= query_params.min_score)
        if query_params.max_score is not None:
            conditions.append(Content.score <= query_params.max_score)

        # 时间筛选
        if query_params.publish_date_start:
            conditions.append(Content.publish_time >= query_params.publish_date_start)
        if query_params.publish_date_end:
            conditions.append(Content.publish_time <= query_params.publish_date_end)
        if query_params.create_date_start:
            conditions.append(Content.create_time >= query_params.create_date_start)
        if query_params.create_date_end:
            conditions.append(Content.create_time <= query_params.create_date_end)

        # 付费筛选
        if query_params.is_free is not None:
            conditions.append(Content.is_free == query_params.is_free)
        if query_params.is_vip_free is not None:
            conditions.append(Content.is_vip_free == query_params.is_vip_free)

        # 标签筛选
        if query_params.tags:
            tag_list = [tag.strip() for tag in query_params.tags.split(",")]
            for tag in tag_list:
                conditions.append(Content.tags.contains(tag))

        stmt = select(Content).where(and_(*conditions))

        # 排序
        if query_params.sort_by == "create_time":
            order_by = Content.create_time
        elif query_params.sort_by == "update_time":
            order_by = Content.update_time
        elif query_params.sort_by == "publish_time":
            order_by = Content.publish_time
        elif query_params.sort_by == "view_count":
            order_by = Content.view_count
        elif query_params.sort_by == "like_count":
            order_by = Content.like_count
        elif query_params.sort_by == "favorite_count":
            order_by = Content.favorite_count
        elif query_params.sort_by == "comment_count":
            order_by = Content.comment_count
        elif query_params.sort_by == "score":
            order_by = Content.score
        else:
            order_by = Content.create_time

        if query_params.sort_order == "asc":
            stmt = stmt.order_by(order_by.asc())
        else:
            stmt = stmt.order_by(order_by.desc())

        # 计算总数
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar()

        # 分页查询
        stmt = stmt.offset(pagination.offset).limit(pagination.limit)
        result = await self.db.execute(stmt)
        contents = result.scalars().all()

        content_info_list = [ContentInfo.model_validate(content) for content in contents]

        pagination_result = PaginationResult.create(
            items=content_info_list,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )

        # 缓存结果（短期缓存）
        await cache_service.set(cache_key, pagination_result.model_dump(), ttl=300)

        return pagination_result

    @atomic_lock(lambda *args, **kwargs: f"content:stats:{kwargs.get('content_id')}")
    async def increment_content_stats(self, content_id: int, stat_type: str, increment_value: int = 1) -> bool:
        """增加内容统计数据 - 带分布式锁"""
        try:
            # 更新数据库
            if stat_type == "view_count":
                await self.db.execute(update(Content).where(Content.id == content_id).values(view_count=Content.view_count + increment_value))
            elif stat_type == "like_count":
                await self.db.execute(update(Content).where(Content.id == content_id).values(like_count=Content.like_count + increment_value))
            elif stat_type == "favorite_count":
                await self.db.execute(update(Content).where(Content.id == content_id).values(favorite_count=Content.favorite_count + increment_value))
            elif stat_type == "comment_count":
                await self.db.execute(update(Content).where(Content.id == content_id).values(comment_count=Content.comment_count + increment_value))
            elif stat_type == "share_count":
                await self.db.execute(update(Content).where(Content.id == content_id).values(share_count=Content.share_count + increment_value))
            else:
                raise BusinessException("不支持的统计类型")

            await self.db.commit()

            # 清除相关缓存
            await cache_service.delete_content_cache(content_id)
            await cache_service.delete_pattern("content:*")

            return True
        except Exception as e:
            await self.db.rollback()
            raise BusinessException(f"更新统计数据失败: {str(e)}")

    @atomic_optimistic("t_content", "content_id")
    async def score_content(self, content_id: int, user_id: int, score_request: ScoreContentRequest) -> bool:
        """为内容评分 - 带乐观锁"""
        # 检查幂等性
        cached_result = await cache_service.check_idempotent(user_id, "score_content", content_id, score_request.score)
        if cached_result is not None:
            return cached_result.get("success", False)

        content = (await self.db.execute(select(Content).where(Content.id == content_id))).scalar_one_or_none()
        if not content:
            raise BusinessException("内容不存在")

        # 验证评分范围
        if not (1 <= score_request.score <= 5):
            raise BusinessException("评分必须在1-5之间")

        # 更新评分（这里简化处理，实际可能需要更复杂的评分算法）
        new_score = (content.score * content.score_count + score_request.score) / (content.score_count + 1)
        new_score_count = content.score_count + 1

        await self.db.execute(update(Content).where(Content.id == content_id).values(
            score=new_score,
            score_count=new_score_count
        ))
        await self.db.commit()

        # 清除相关缓存
        await cache_service.delete_content_cache(content_id)
        await cache_service.delete_pattern("content:*")

        # 缓存幂等性结果
        result = {"success": True, "new_score": new_score, "new_score_count": new_score_count}
        await cache_service.set_idempotent_result(user_id, "score_content", result, content_id, score_request.score)

        return True

    # ================ 章节相关方法 ================

    @atomic_transaction()
    async def create_chapter(self, chapter_data: ChapterCreate, user_id: int) -> ChapterInfo:
        """创建章节 - 带原子性事务"""
        # 验证内容所有权
        content = (await self.db.execute(select(Content).where(Content.id == chapter_data.content_id))).scalar_one_or_none()
        if not content:
            raise BusinessException("内容不存在")
        if content.author_id != user_id:
            raise BusinessException("无权限为此内容创建章节")

        # 检查章节号是否重复
        existing_chapter = (await self.db.execute(
            select(Chapter).where(and_(Chapter.content_id == chapter_data.content_id, Chapter.chapter_num == chapter_data.chapter_num))
        )).scalar_one_or_none()
        if existing_chapter:
            raise BusinessException("章节号已存在")

        chapter = Chapter(
            content_id=chapter_data.content_id,
            chapter_num=chapter_data.chapter_num,
            title=chapter_data.title,
            content=chapter_data.content,
            word_count=chapter_data.word_count or len(chapter_data.content),
            status="DRAFT"
        )

        self.db.add(chapter)
        await self.db.commit()
        await self.db.refresh(chapter)

        # 清除相关缓存
        await cache_service.delete_pattern("chapter:*")
        await cache_service.delete_content_cache(chapter_data.content_id)

        return ChapterInfo.model_validate(chapter)

    async def get_content_chapters(self, content_id: int, user_id: Optional[int] = None) -> List[ChapterListItem]:
        """获取内容章节列表 - 带缓存"""
        # 尝试从缓存获取
        cache_key = f"chapters:content:{content_id}"
        cached_chapters = await cache_service.get(cache_key)
        if cached_chapters:
            return [ChapterListItem.model_validate(chapter) for chapter in cached_chapters]

        # 缓存未命中，从数据库获取
        chapters = (await self.db.execute(
            select(Chapter).where(Chapter.content_id == content_id).order_by(Chapter.chapter_num)
        )).scalars().all()

        chapter_list = [ChapterListItem.model_validate(chapter) for chapter in chapters]

        # 缓存结果
        await cache_service.set(cache_key, [chapter.model_dump() for chapter in chapter_list], ttl=1800)

        return chapter_list

    # ================ 付费相关方法 ================

    @atomic_transaction()
    async def create_content_payment(self, content_id: int, payment_data: ContentPaymentCreate, user_id: int) -> ContentPaymentInfo:
        """创建付费配置 - 带原子性事务"""
        # 验证内容所有权
        content = (await self.db.execute(select(Content).where(Content.id == content_id))).scalar_one_or_none()
        if not content:
            raise BusinessException("内容不存在")
        if content.author_id != user_id:
            raise BusinessException("无权限为此内容创建付费配置")

        # 检查是否已存在付费配置
        existing_payment = (await self.db.execute(
            select(ContentPayment).where(ContentPayment.content_id == content_id)
        )).scalar_one_or_none()
        if existing_payment:
            raise BusinessException("该内容已有付费配置")

        payment = ContentPayment(
            content_id=content_id,
            payment_type=payment_data.payment_type,
            price=payment_data.price,
            coin_price=payment_data.coin_price,
            vip_discount=payment_data.vip_discount,
            trial_duration=payment_data.trial_duration,
            expire_days=payment_data.expire_days
        )

        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)

        # 清除相关缓存
        await cache_service.delete_pattern("payment:*")
        await cache_service.delete_content_cache(content_id)

        return ContentPaymentInfo.model_validate(payment)

    async def get_content_payment(self, content_id: int) -> Optional[ContentPaymentInfo]:
        """获取内容付费配置 - 带缓存"""
        # 尝试从缓存获取
        cache_key = f"payment:content:{content_id}"
        cached_payment = await cache_service.get(cache_key)
        if cached_payment:
            return ContentPaymentInfo.model_validate(cached_payment)

        # 缓存未命中，从数据库获取
        payment = (await self.db.execute(
            select(ContentPayment).where(ContentPayment.content_id == content_id)
        )).scalar_one_or_none()

        if payment:
            payment_info = ContentPaymentInfo.model_validate(payment)
            # 缓存结果
            await cache_service.set(cache_key, payment_info.model_dump(), ttl=3600)
            return payment_info

        return None

    # ================ 聚合查询方法 ================

    async def get_content_list_by_category_name(self, category_name: str, match: str, query_params: ContentQueryParams, pagination: PaginationParams) -> PaginationResult[ContentInfo]:
        """根据分类名称查询内容 - 带缓存"""
        # 生成缓存键
        cache_key = f"content:category:{category_name}:{match}:{hash(str(query_params.model_dump()) + str(pagination.model_dump()))}"
        
        # 尝试从缓存获取
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            return PaginationResult.create(**cached_result)

        # 这里需要关联分类表查询，简化处理
        # 实际实现中需要根据分类名称查询分类ID，然后查询内容
        
        # 模拟查询结果
        contents = []
        total = 0

        pagination_result = PaginationResult.create(
            items=contents,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )

        # 缓存结果（短期缓存）
        await cache_service.set(cache_key, pagination_result.model_dump(), ttl=300)

        return pagination_result
