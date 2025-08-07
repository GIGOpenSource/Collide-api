"""
自定义异常类
"""
from typing import Any, Optional


class BusinessException(Exception):
    """业务异常基类"""
    
    def __init__(
        self,
        message: str = "业务操作失败",
        code: int = 400,
        data: Optional[Any] = None
    ):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(self.message)


class UserException(BusinessException):
    """用户相关异常"""
    pass


class UserNotFoundError(UserException):
    """用户不存在异常"""
    
    def __init__(self, message: str = "用户不存在"):
        super().__init__(message=message, code=1001)


class UserAlreadyExistsError(UserException):
    """用户已存在异常"""
    
    def __init__(self, message: str = "用户已存在"):
        super().__init__(message=message, code=1002)


class InvalidCredentialsError(UserException):
    """登录凭证无效异常"""
    
    def __init__(self, message: str = "用户名或密码错误"):
        super().__init__(message=message, code=1003)


class InsufficientBalanceError(BusinessException):
    """余额不足异常"""
    
    def __init__(self, message: str = "余额不足"):
        super().__init__(message=message, code=1004)


class OperationFailedError(BusinessException):
    """操作失败异常"""
    
    def __init__(self, message: str = "操作失败"):
        super().__init__(message=message, code=1005)


class ContentException(BusinessException):
    """内容相关异常"""
    pass


class ContentNotFoundError(ContentException):
    """内容不存在异常"""
    
    def __init__(self, message: str = "内容不存在"):
        super().__init__(message=message, code=2001)


class ChapterNotFoundError(ContentException):
    """章节不存在异常"""
    
    def __init__(self, message: str = "章节不存在"):
        super().__init__(message=message, code=2002)


class ContentAccessDeniedError(ContentException):
    """内容访问权限不足异常"""
    
    def __init__(self, message: str = "内容访问权限不足"):
        super().__init__(message=message, code=2003)