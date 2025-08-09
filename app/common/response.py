"""
统一响应模型
按照用户要求的格式定义标准响应体、错误体、分页体

使用示例：
1. 成功响应：
   {
     "code": 200,
     "message": "操作成功",
     "success": true,
     "data": {...}
   }

2. 错误响应：
   {
     "code": 400,
     "message": "某某函数失败",
     "success": false,
     "data": null
   }

3. 分页响应：
   {
     "code": 200,
     "message": "获取成功",
     "success": true,
     "data": {
       "list": [...],
       "total": 100,
       "currentPage": 1,
       "pageSize": 20,
       "totalPage": 5
     }
   }
"""
from typing import Any, Optional, Generic, TypeVar, List
from pydantic import BaseModel, Field

T = TypeVar('T')


class BaseResponse(BaseModel, Generic[T]):
    """基础响应模型"""
    code: int = Field(description="响应状态码")
    message: str = Field(description="响应消息")
    success: bool = Field(description="操作是否成功")
    data: Optional[T] = Field(default=None, description="响应数据")


class SuccessResponse(BaseResponse[T]):
    """成功响应模型
    
    成功体格式：
    {
      "code": 200,
      "message": "success",
      "data": {...},
      "success": true
    }
    """
    code: int = 200
    message: str = "操作成功"
    success: bool = True
    
    @classmethod
    def create(cls, data: T = None, message: str = "操作成功") -> "SuccessResponse[T]":
        """创建成功响应"""
        return cls(data=data, message=message)


class ErrorResponse(BaseResponse[None]):
    """错误响应模型
    
    错误体格式：
    {
      "code": 400,
      "message": "error message",
      "data": null,
      "success": false
    }
    """
    success: bool = False
    data: None = None
    
    @classmethod
    def create(cls, code: int = 400, message: str = "操作失败") -> "ErrorResponse":
        """创建错误响应"""
        return cls(code=code, message=message)


class PaginationData(BaseModel, Generic[T]):
    """分页数据模型"""
    list: List[T] = Field(description="分页数据列表")
    total: int = Field(description="总记录数")
    current_page: int = Field(alias="currentPage", description="当前页码")
    page_size: int = Field(alias="pageSize", description="每页大小")
    total_page: int = Field(alias="totalPage", description="总页数")
    
    model_config = {"populate_by_name": True}


class PaginationResponse(BaseResponse[PaginationData[T]], Generic[T]):
    """分页响应模型
    
    分页体格式：
    {
      "success": true,
      "code": "200",
      "message": "操作成功",
      "data": {
        "list": {},
        "total": 100,
        "currentPage": 1,
        "pageSize": 20,
        "totalPage": 5
      }
    }
    """
    code: int = 200
    message: str = "操作成功"
    success: bool = True
    
    @classmethod
    def from_pagination_result(
        cls,
        result: "PaginationResult[T]",
        message: str = "操作成功"
    ) -> "PaginationResponse[T]":
        """从通用分页结果构造统一分页响应"""
        pagination_data = PaginationData[T](
            list=result.items,
            total=result.total,
            current_page=result.page,
            page_size=result.page_size,
            total_page=result.total_pages
        )
        return cls(data=pagination_data, message=message)

    @classmethod
    def create(
        cls,
        datas: List[T],
        total: int,
        current_page: int,
        page_size: int,
        message: str = "操作成功"
    ) -> "PaginationResponse[T]":
        """创建分页响应"""
        total_page = (total + page_size - 1) // page_size if total > 0 else 0
        
        pagination_data = PaginationData[T](
            list=datas,
            total=total,
            current_page=current_page,
            page_size=page_size,
            total_page=total_page
        )
        
        return cls(data=pagination_data, message=message)


# 响应码常量
class ResponseCode:
    """响应码常量"""
    SUCCESS = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_ERROR = 500
    
    # 业务错误码
    USER_NOT_FOUND = 1001
    USER_ALREADY_EXISTS = 1002
    INVALID_CREDENTIALS = 1003
    INSUFFICIENT_BALANCE = 1004
    OPERATION_FAILED = 1005


# 统一错误处理工具函数
def handle_error_response(code: int = 400, message: str = "操作失败") -> ErrorResponse:
    """统一错误响应处理
    
    返回格式：
    {
      "code": 400,
      "message": "某某函数失败",
      "success": false,
      "data": null
    }
    """
    return ErrorResponse.create(code=code, message=message)


def handle_business_error(message: str, code: int = 400) -> ErrorResponse:
    """业务错误响应处理"""
    return handle_error_response(code=code, message=message)


def handle_system_error(message: str = "系统内部错误") -> ErrorResponse:
    """系统错误响应处理"""
    return handle_error_response(code=500, message=message)


def handle_not_found_error(message: str = "资源不存在") -> ErrorResponse:
    """资源不存在错误响应处理"""
    return handle_error_response(code=404, message=message)


def handle_unauthorized_error(message: str = "未授权访问") -> ErrorResponse:
    """未授权错误响应处理"""
    return handle_error_response(code=401, message=message)


def handle_forbidden_error(message: str = "禁止访问") -> ErrorResponse:
    """禁止访问错误响应处理"""
    return handle_error_response(code=403, message=message)


# 使用示例和最佳实践
"""
在路由中使用统一错误响应的最佳实践：

1. 业务异常处理：
   try:
       result = await service.some_operation()
       return SuccessResponse.create(data=result, message="操作成功")
   except BusinessException as e:
       return handle_business_error(e.message, e.code)
   except Exception as e:
       logger.error(f"操作失败: {str(e)}")
       return handle_system_error("操作失败，请稍后重试")

2. 不同错误类型：
   - 业务错误：handle_business_error("用户名已存在", 1002)
   - 系统错误：handle_system_error("系统内部错误")
   - 资源不存在：handle_not_found_error("用户不存在")
   - 未授权：handle_unauthorized_error("请先登录")
   - 禁止访问：handle_forbidden_error("无权限访问")

3. 确保所有错误响应都遵循统一格式：
   {
     "code": 400,
     "message": "某某函数失败",
     "success": false,
     "data": null
   }
"""