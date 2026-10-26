
# 프로젝트 전역 Exception
# 과거 프로젝트에서 사용했던 ControllerException과 ServiceException을 조합

# 사용시 raise AppException() 형태로 사용
class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500, # HTTP Status Code Internal Server Error
    ) -> None:
        super().__init__(message)

        self.code = code
        self.message = message
        self.status_code = status_code

# HttpClient에서 오류 발생 시 처리
class HttpClientException(Exception):
    def __init__(
        self,
        message: str,
        url: str | None = None,
    ):
        super().__init__(message)
        self.url = url