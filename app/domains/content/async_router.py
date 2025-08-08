"""
内容模块异步API路由
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_async_db
from app.common.dependencies import get_current_user_context, UserContext, get_optional_user_context
from app.common.response import SuccessResponse, PaginationResponse
from app.common.pagination import PaginationParams
from app.domains.content.async_service import ContentAsyncService
from app.domains.content.schemas import (
    ContentCreate, ContentUpdate, ContentInfo, ContentQueryParams,
    ChapterCreate, ChapterUpdate, ChapterInfo, ChapterListItem,
    ContentPaymentCreate, ContentPaymentUpdate, ContentPaymentInfo,
    UserContentPurchaseCreate, UserContentPurchaseInfo,
    PublishContentRequest, ContentStatsUpdate, ScoreContentRequest
)

router = APIRouter(prefix="/api/v1/content", tags=["内容管理"])


# ================ 内容管理接口 ================

@router.post("/", response_model=SuccessResponse[ContentInfo], summary="创建内容", description="创建新的内容（小说、漫画、视频等）")
async def create_content(
    content_data: ContentCreate,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db)
):
    """
    创建内容
    
    - **title**: 内容标题（必填）
    - **description**: 内容描述
    - **content_type**: 内容类型（NOVEL、COMIC、VIDEO、ARTICLE、AUDIO）
    - **content_data**: 内容数据URL
    - **cover_url**: 封面图片URL
    - **tags**: 标签，逗号分隔
    - **category_id**: 分类ID
    - **category_name**: 分类名称
    
    需要登录权限，创建的内容会自动设置为草稿状态。
    """
    service = ContentAsyncService(db)
    content = await service.create_content(
        content_data, 
        current_user.user_id, 
        current_user.username
    )
    return SuccessResponse(data=content, message="内容创建成功")


@router.get("/{content_id}", response_model=SuccessResponse[ContentInfo], summary="获取内容详情", description="根据内容ID获取详细信息")
async def get_content(
    content_id: int,
    current_user: Optional[UserContext] = Depends(get_optional_user_context),
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取内容详情
    
    根据内容ID获取完整的内容信息，包括：
    - 基本信息（标题、描述、类型等）
    - 作者信息
    - 统计数据（浏览量、点赞数、评分等）
    - 发布状态和审核状态
    
    如果用户已登录，会自动增加浏览量。
    """
    service = ContentAsyncService(db)
    user_id = current_user.user_id if current_user else None
    content = await service.get_content_by_id(content_id, user_id)
    return SuccessResponse(data=content, message="获取成功")


@router.put("/{content_id}", response_model=SuccessResponse[ContentInfo], summary="更新内容", description="更新已有内容信息")
async def update_content(
    content_id: int,
    content_data: ContentUpdate,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db)
):
    """
    更新内容
    
    更新指定内容的信息，只有内容作者可以执行此操作。
    
    可更新的字段：
    - **title**: 内容标题
    - **description**: 内容描述
    - **content_data**: 内容数据URL
    - **cover_url**: 封面图片URL
    - **tags**: 标签
    - **category_id**: 分类ID
    - **category_name**: 分类名称
    - **status**: 状态（DRAFT、PUBLISHED、OFFLINE）
    
    需要登录权限且只能更新自己的内容。
    """
    service = ContentAsyncService(db)
    content = await service.update_content(content_id, content_data, current_user.user_id)
    return SuccessResponse(data=content, message="内容更新成功")


@router.delete("/{content_id}", response_model=SuccessResponse[bool])
async def delete_content(
    content_id: int,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db)
):
    """删除内容"""
    service = ContentAsyncService(db)
    result = await service.delete_content(content_id, current_user.user_id)
    return SuccessResponse(data=result, message="内容删除成功")


@router.post("/{content_id}/publish", response_model=SuccessResponse[ContentInfo])
async def publish_content(
    content_id: int,
    publish_request: PublishContentRequest,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db)
):
    """发布内容"""
    service = ContentAsyncService(db)
    content = await service.publish_content(content_id, current_user.user_id, publish_request)
    return SuccessResponse(data=content, message="内容发布成功")


@router.get("/", response_model=PaginationResponse[ContentInfo], summary="获取内容列表", description="支持多种筛选条件的内容列表查询")
async def get_content_list(
    # 基础筛选参数
    content_type: Optional[str] = Query(None, description="内容类型：NOVEL(小说)、COMIC(漫画)、VIDEO(视频)、ARTICLE(文章)、AUDIO(音频)"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    author_id: Optional[int] = Query(None, description="作者用户ID"),
    status: Optional[str] = Query(None, description="内容状态：DRAFT(草稿)、PUBLISHED(已发布)、OFFLINE(下线)"),
    review_status: Optional[str] = Query(None, description="审核状态：PENDING(待审核)、APPROVED(已通过)、REJECTED(已拒绝)"),
    keyword: Optional[str] = Query(None, description="关键词搜索（标题、描述、标签、作者昵称）"),
    
    # 统计数据筛选参数
    min_view_count: Optional[int] = Query(None, ge=0, description="最小浏览量"),
    max_view_count: Optional[int] = Query(None, ge=0, description="最大浏览量"),
    min_like_count: Optional[int] = Query(None, ge=0, description="最小点赞数"),
    max_like_count: Optional[int] = Query(None, ge=0, description="最大点赞数"),
    min_favorite_count: Optional[int] = Query(None, ge=0, description="最小收藏数"),
    max_favorite_count: Optional[int] = Query(None, ge=0, description="最大收藏数"),
    min_comment_count: Optional[int] = Query(None, ge=0, description="最小评论数"),
    max_comment_count: Optional[int] = Query(None, ge=0, description="最大评论数"),
    min_score: Optional[float] = Query(None, ge=0, le=5, description="最低评分（1-5分）"),
    max_score: Optional[float] = Query(None, ge=0, le=5, description="最高评分（1-5分）"),
    
    # 时间筛选参数
    publish_date_start: Optional[str] = Query(None, description="发布开始日期，格式：YYYY-MM-DD"),
    publish_date_end: Optional[str] = Query(None, description="发布结束日期，格式：YYYY-MM-DD"),
    create_date_start: Optional[str] = Query(None, description="创建开始日期，格式：YYYY-MM-DD"),
    create_date_end: Optional[str] = Query(None, description="创建结束日期，格式：YYYY-MM-DD"),
    
    # 付费筛选参数
    is_free: Optional[bool] = Query(None, description="是否筛选免费内容"),
    is_vip_free: Optional[bool] = Query(None, description="是否筛选会员免费内容"),
    
    # 标签筛选
    tags: Optional[str] = Query(None, description="标签筛选，多个标签用逗号分隔，如：玄幻,修仙,热血"),
    
    # 排序和分页参数
    sort_by: str = Query("create_time", description="排序字段：create_time(创建时间), update_time(更新时间), publish_time(发布时间), view_count(浏览量), like_count(点赞数), favorite_count(收藏数), comment_count(评论数), score(评分)"),
    sort_order: str = Query("desc", description="排序方向：asc(升序), desc(降序)"),
    page: int = Query(1, ge=1, description="页码，从1开始"),
    size: int = Query(20, ge=1, le=100, description="每页显示数量，最大100"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取内容列表 - 支持多维度筛选和排序
    
    这是一个功能强大的内容查询接口，支持：
    
    ## 基础筛选
    - **内容类型**: 小说、漫画、视频、文章、音频
    - **分类筛选**: 根据分类ID筛选
    - **作者筛选**: 查看指定作者的作品
    - **状态筛选**: 草稿、已发布、已下线
    - **关键词搜索**: 在标题、描述、标签中搜索
    
    ## 统计数据筛选
    - **热度筛选**: 根据浏览量、点赞数、收藏数等
    - **质量筛选**: 根据评分筛选高质量内容
    
    ## 时间范围筛选
    - 根据发布时间或创建时间筛选
    
    ## 付费属性筛选
    - 免费内容筛选
    - 会员免费内容筛选
    
    ## 标签筛选
    - 支持多标签组合筛选
    
    ## 排序选项
    - 支持多种排序方式：时间、热度、评分等
    - 升序或降序排列
    
    返回分页结果，包含总数、当前页、总页数等信息。
    """
    service = ContentAsyncService(db)
    query_params = ContentQueryParams(
        content_type=content_type,
        category_id=category_id,
        author_id=author_id,
        status=status,
        review_status=review_status,
        keyword=keyword,
        min_view_count=min_view_count,
        max_view_count=max_view_count,
        min_like_count=min_like_count,
        max_like_count=max_like_count,
        min_favorite_count=min_favorite_count,
        max_favorite_count=max_favorite_count,
        min_comment_count=min_comment_count,
        max_comment_count=max_comment_count,
        min_score=min_score,
        max_score=max_score,
        publish_date_start=publish_date_start,
        publish_date_end=publish_date_end,
        create_date_start=create_date_start,
        create_date_end=create_date_end,
        is_free=is_free,
        is_vip_free=is_vip_free,
        tags=tags,
        sort_by=sort_by,
        sort_order=sort_order
    )
    pagination = PaginationParams(page=page, size=size)
    result = await service.get_content_list(query_params, pagination)
    return PaginationResponse.from_pagination_result(result, "获取成功")


@router.post("/{content_id}/stats", response_model=SuccessResponse[bool])
async def update_content_stats(
    content_id: int,
    stats_update: ContentStatsUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """更新内容统计数据"""
    service = ContentAsyncService(db)
    result = await service.increment_content_stats(
        content_id, 
        stats_update.increment_type, 
        stats_update.increment_value
    )
    return SuccessResponse(data=result, message="统计更新成功")


@router.post("/{content_id}/score", response_model=SuccessResponse[bool])
async def score_content(
    content_id: int,
    score_request: ScoreContentRequest,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db)
):
    """为内容评分"""
    service = ContentAsyncService(db)
    result = await service.score_content(content_id, current_user.user_id, score_request)
    return SuccessResponse(data=result, message="评分成功")


# ================ 章节管理接口 ================

@router.post("/{content_id}/chapters", response_model=SuccessResponse[ChapterInfo], summary="创建章节", description="为指定内容创建新章节")
async def create_chapter(
    content_id: int,
    chapter_data: ChapterCreate,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db)
):
    """
    创建章节
    
    为指定的内容（如小说、漫画）添加新章节。
    
    ## 参数说明
    - **content_id**: 内容ID（路径参数）
    - **chapter_num**: 章节号（必须唯一）
    - **title**: 章节标题
    - **content**: 章节内容
    - **word_count**: 字数统计
    
    ## 权限要求
    - 需要登录
    - 只能为自己的内容创建章节
    - 章节号不能重复
    
    新创建的章节默认为草稿状态。
    """
    # 确保content_id一致
    chapter_data.content_id = content_id
    service = ContentAsyncService(db)
    chapter = await service.create_chapter(chapter_data, current_user.user_id)
    return SuccessResponse(data=chapter, message="章节创建成功")


@router.get("/{content_id}/chapters", response_model=SuccessResponse[List[ChapterListItem]])
async def get_content_chapters(
    content_id: int,
    current_user: Optional[UserContext] = Depends(get_optional_user_context),
    db: AsyncSession = Depends(get_async_db)
):
    """获取内容的章节列表"""
    service = ContentAsyncService(db)
    user_id = current_user.user_id if current_user else None
    chapters = await service.get_content_chapters(content_id, user_id)
    return SuccessResponse(data=chapters, message="获取成功")


@router.get("/chapters/{chapter_id}", response_model=SuccessResponse[ChapterInfo])
async def get_chapter(
    chapter_id: int,
    current_user: Optional[UserContext] = Depends(get_optional_user_context),
    db: AsyncSession = Depends(get_async_db)
):
    """获取章节详情"""
    service = ContentAsyncService(db)
    user_id = current_user.user_id if current_user else None
    chapter = await service.get_chapter_by_id(chapter_id, user_id)
    return SuccessResponse(data=chapter, message="获取成功")


@router.put("/chapters/{chapter_id}", response_model=SuccessResponse[ChapterInfo])
async def update_chapter(
    chapter_id: int,
    chapter_data: ChapterUpdate,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db)
):
    """更新章节"""
    service = ContentAsyncService(db)
    chapter = await service.update_chapter(chapter_id, chapter_data, current_user.user_id)
    return SuccessResponse(data=chapter, message="章节更新成功")


@router.delete("/chapters/{chapter_id}", response_model=SuccessResponse[bool])
async def delete_chapter(
    chapter_id: int,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db)
):
    """删除章节"""
    service = ContentAsyncService(db)
    result = await service.delete_chapter(chapter_id, current_user.user_id)
    return SuccessResponse(data=result, message="章节删除成功")


# ================ 付费配置接口 ================

@router.post("/{content_id}/payment", response_model=SuccessResponse[ContentPaymentInfo])
async def create_content_payment(
    content_id: int,
    payment_data: ContentPaymentCreate,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db)
):
    """创建内容付费配置"""
    # 确保content_id一致
    payment_data.content_id = content_id
    service = ContentAsyncService(db)
    payment = await service.create_content_payment(payment_data, current_user.user_id)
    return SuccessResponse(data=payment, message="付费配置创建成功")


@router.get("/{content_id}/payment", response_model=SuccessResponse[Optional[ContentPaymentInfo]])
async def get_content_payment(
    content_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """获取内容付费配置"""
    service = ContentAsyncService(db)
    payment = await service.get_content_payment(content_id)
    return SuccessResponse(data=payment, message="获取成功")


# ================ 购买相关接口 ================

@router.post("/{content_id}/purchase", response_model=SuccessResponse[UserContentPurchaseInfo], summary="购买内容", description="购买付费内容")
async def create_purchase_record(
    content_id: int,
    purchase_data: UserContentPurchaseCreate,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db)
):
    """
    购买内容
    
    购买指定的付费内容，创建购买记录。
    
    ## 购买流程
    1. 检查内容是否存在
    2. 验证是否已购买
    3. 扣除用户金币
    4. 创建购买记录
    5. 获得内容访问权限
    
    ## 参数说明
    - **content_id**: 要购买的内容ID
    - **coin_amount**: 支付的金币数量
    - **order_id**: 关联的订单ID（可选）
    - **order_no**: 订单号（可选）
    
    ## 权限要求
    - 需要登录
    - 账户金币余额充足
    - 内容未被购买过
    
    购买成功后，用户将获得永久或限时的内容访问权限。
    """
    # 确保content_id一致
    purchase_data.content_id = content_id
    service = ContentAsyncService(db)
    purchase = await service.create_purchase_record(purchase_data, current_user.user_id)
    return SuccessResponse(data=purchase, message="购买成功")


@router.get("/{content_id}/purchase", response_model=SuccessResponse[Optional[UserContentPurchaseInfo]])
async def check_user_purchase(
    content_id: int,
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db)
):
    """检查用户是否购买了内容"""
    service = ContentAsyncService(db)
    purchase = await service.check_user_purchase(current_user.user_id, content_id)
    return SuccessResponse(data=purchase, message="检查完成")


@router.get("/purchases/my", response_model=PaginationResponse[UserContentPurchaseInfo])
async def get_my_purchases(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db)
):
    """获取我的购买记录"""
    service = ContentAsyncService(db)
    pagination = PaginationParams(page=page, size=size)
    result = await service.get_user_purchases(current_user.user_id, pagination)
    return PaginationResponse.from_pagination_result(result, "获取成功")


# ================ 我的内容管理接口 ================

@router.get("/my/contents", response_model=PaginationResponse[ContentInfo], summary="我的内容列表", description="获取当前用户创建的所有内容")
async def get_my_contents(
    # 基础筛选参数
    content_type: Optional[str] = Query(None, description="内容类型：NOVEL、COMIC、VIDEO、ARTICLE、AUDIO"),
    status: Optional[str] = Query(None, description="内容状态：DRAFT、PUBLISHED、OFFLINE"),
    review_status: Optional[str] = Query(None, description="审核状态：PENDING、APPROVED、REJECTED"),
    keyword: Optional[str] = Query(None, description="关键词搜索（标题、描述、标签）"),
    
    # 统计数据筛选参数
    min_view_count: Optional[int] = Query(None, ge=0, description="最小浏览量"),
    max_view_count: Optional[int] = Query(None, ge=0, description="最大浏览量"),
    min_like_count: Optional[int] = Query(None, ge=0, description="最小点赞数"),
    max_like_count: Optional[int] = Query(None, ge=0, description="最大点赞数"),
    min_favorite_count: Optional[int] = Query(None, ge=0, description="最小收藏数"),
    max_favorite_count: Optional[int] = Query(None, ge=0, description="最大收藏数"),
    min_score: Optional[float] = Query(None, ge=0, le=5, description="最低评分"),
    max_score: Optional[float] = Query(None, ge=0, le=5, description="最高评分"),
    
    # 时间筛选参数
    publish_date_start: Optional[str] = Query(None, description="发布开始日期，格式：YYYY-MM-DD"),
    publish_date_end: Optional[str] = Query(None, description="发布结束日期，格式：YYYY-MM-DD"),
    create_date_start: Optional[str] = Query(None, description="创建开始日期，格式：YYYY-MM-DD"),
    create_date_end: Optional[str] = Query(None, description="创建结束日期，格式：YYYY-MM-DD"),
    
    # 标签筛选
    tags: Optional[str] = Query(None, description="标签筛选，多个标签用逗号分隔"),
    
    # 排序和分页参数
    sort_by: str = Query("create_time", description="排序字段：create_time、update_time、publish_time、view_count、like_count、favorite_count、comment_count、score"),
    sort_order: str = Query("desc", description="排序方向：asc(升序)、desc(降序)"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: UserContext = Depends(get_current_user_context),
    db: AsyncSession = Depends(get_async_db)
):
    """
    我的内容列表 - 内容创作者管理界面
    
    获取当前登录用户创建的所有内容，支持多维度筛选和排序。
    
    ## 功能特性
    - **内容管理**: 查看所有自己创建的内容
    - **状态筛选**: 按发布状态、审核状态筛选
    - **性能分析**: 按浏览量、点赞数、评分等筛选
    - **时间管理**: 按创建时间、发布时间筛选
    - **搜索功能**: 在自己的内容中搜索
    
    ## 使用场景
    - 作者查看自己的作品列表
    - 筛选待发布的草稿
    - 查看高热度作品
    - 分析作品表现数据
    - 管理不同类型的内容
    
    ## 权限说明
    - 需要登录
    - 只能查看自己创建的内容
    - 包含所有状态的内容（草稿、已发布、下线等）
    
    返回分页结果，支持所有内容查询的筛选和排序功能。
    """
    service = ContentAsyncService(db)
    query_params = ContentQueryParams(
        content_type=content_type,
        author_id=current_user.user_id,  # 只获取当前用户的内容
        status=status,
        review_status=review_status,
        keyword=keyword,
        min_view_count=min_view_count,
        max_view_count=max_view_count,
        min_like_count=min_like_count,
        max_like_count=max_like_count,
        min_favorite_count=min_favorite_count,
        max_favorite_count=max_favorite_count,
        min_score=min_score,
        max_score=max_score,
        publish_date_start=publish_date_start,
        publish_date_end=publish_date_end,
        create_date_start=create_date_start,
        create_date_end=create_date_end,
        tags=tags,
        sort_by=sort_by,
        sort_order=sort_order
    )
    pagination = PaginationParams(page=page, size=size)
    result = await service.get_content_list(query_params, pagination)
    return PaginationResponse.from_pagination_result(result, "获取成功")


# ================ 内容统计接口 ================

@router.get("/{content_id}/stats", response_model=SuccessResponse[dict])
async def get_content_stats(
    content_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """获取内容统计信息"""
    service = ContentAsyncService(db)
    content = await service.get_content_by_id(content_id)
    
    stats = {
        "view_count": content.view_count,
        "like_count": content.like_count,
        "comment_count": content.comment_count,
        "share_count": content.share_count,
        "favorite_count": content.favorite_count,
        "score_count": content.score_count,
        "score_total": content.score_total,
        "average_score": content.average_score
    }
    
    return SuccessResponse(data=stats, message="获取成功")


# ================ 特色内容接口 ================

@router.get("/hot", response_model=PaginationResponse[ContentInfo], summary="获取热门内容", description="获取指定时间内的热门内容")
async def get_hot_contents(
    content_type: Optional[str] = Query(None, description="内容类型：NOVEL、COMIC、VIDEO、ARTICLE、AUDIO"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    days: int = Query(7, ge=1, le=365, description="统计天数，默认7天，最大365天"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取热门内容
    
    返回指定时间范围内的热门内容，按浏览量排序。
    
    - 只显示已发布且审核通过的内容
    - 可按内容类型和分类筛选
    - 可自定义统计时间范围（1-365天）
    - 按浏览量降序排列
    
    热门度计算基于指定天数内的内容表现。
    """
    service = ContentAsyncService(db)
    
    # 计算时间范围
    from datetime import datetime, timedelta
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    query_params = ContentQueryParams(
        content_type=content_type,
        category_id=category_id,
        status="PUBLISHED",
        review_status="APPROVED",
        publish_date_start=start_date,
        sort_by="view_count",  # 可以后续改为综合热度算法
        sort_order="desc"
    )
    pagination = PaginationParams(page=page, size=size)
    result = await service.get_content_list(query_params, pagination)
    return PaginationResponse.from_pagination_result(result, f"获取{days}天内热门内容成功")


@router.get("/latest", response_model=PaginationResponse[ContentInfo])
async def get_latest_contents(
    content_type: Optional[str] = Query(None, description="内容类型"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_async_db)
):
    """获取最新内容 - 按发布时间排序"""
    service = ContentAsyncService(db)
    query_params = ContentQueryParams(
        content_type=content_type,
        category_id=category_id,
        status="PUBLISHED",
        review_status="APPROVED",
        sort_by="publish_time",
        sort_order="desc"
    )
    pagination = PaginationParams(page=page, size=size)
    result = await service.get_content_list(query_params, pagination)
    return PaginationResponse.from_pagination_result(result, "获取最新内容成功")


@router.get("/recommended", response_model=PaginationResponse[ContentInfo])
async def get_recommended_contents(
    content_type: Optional[str] = Query(None, description="内容类型"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_async_db)
):
    """获取推荐内容 - 按评分和热度排序"""
    service = ContentAsyncService(db)
    query_params = ContentQueryParams(
        content_type=content_type,
        category_id=category_id,
        status="PUBLISHED",
        review_status="APPROVED",
        min_score=3.0,  # 至少3分以上
        sort_by="score",
        sort_order="desc"
    )
    pagination = PaginationParams(page=page, size=size)
    result = await service.get_content_list(query_params, pagination)
    return PaginationResponse.from_pagination_result(result, "获取推荐内容成功")


@router.get("/trending", response_model=PaginationResponse[ContentInfo])
async def get_trending_contents(
    content_type: Optional[str] = Query(None, description="内容类型"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_async_db)
):
    """获取趋势内容 - 按点赞数排序"""
    service = ContentAsyncService(db)
    query_params = ContentQueryParams(
        content_type=content_type,
        category_id=category_id,
        status="PUBLISHED",
        review_status="APPROVED",
        min_like_count=10,  # 至少10个点赞
        sort_by="like_count",
        sort_order="desc"
    )
    pagination = PaginationParams(page=page, size=size)
    result = await service.get_content_list(query_params, pagination)
    return PaginationResponse.from_pagination_result(result, "获取趋势内容成功")


@router.get("/search", response_model=PaginationResponse[ContentInfo], summary="搜索内容", description="全文搜索内容，支持标题、描述、标签、作者搜索")
async def search_contents(
    q: str = Query(..., min_length=1, description="搜索关键词，最少1个字符"),
    content_type: Optional[str] = Query(None, description="内容类型：NOVEL、COMIC、VIDEO、ARTICLE、AUDIO"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    sort_by: str = Query("view_count", description="排序字段：create_time(创建时间), update_time(更新时间), publish_time(发布时间), view_count(浏览量), like_count(点赞数), favorite_count(收藏数), comment_count(评论数), score(评分)"),
    sort_order: str = Query("desc", description="排序方向：asc(升序), desc(降序)"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    搜索内容 - 全文搜索
    
    在以下字段中搜索关键词：
    - **标题**: 内容标题
    - **描述**: 内容描述
    - **标签**: 内容标签
    - **作者昵称**: 作者名称
    
    ## 搜索特性
    - 支持中文搜索
    - 支持部分匹配
    - 只搜索已发布且审核通过的内容
    - 可按内容类型和分类进一步筛选
    - 多种排序方式可选
    
    ## 使用示例
    - 搜索"玄幻小说": q=玄幻小说&content_type=NOVEL
    - 搜索作者: q=作者名称
    - 搜索标签: q=修仙
    
    返回匹配的内容列表，按指定方式排序。
    """
    service = ContentAsyncService(db)
    query_params = ContentQueryParams(
        content_type=content_type,
        category_id=category_id,
        status="PUBLISHED",
        review_status="APPROVED",
        keyword=q,
        sort_by=sort_by,
        sort_order=sort_order
    )
    pagination = PaginationParams(page=page, size=size)
    result = await service.get_content_list(query_params, pagination)
    return PaginationResponse.from_pagination_result(result, f"搜索'{q}'的结果")
