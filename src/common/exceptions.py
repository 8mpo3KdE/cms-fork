class DownloadError(IOError):
    pass


class FileFormatNotSupportedException(Exception):
    pass


class GlanceError(Exception):
    def __init__(self, message, status):
        super().__init__(message)
        self.status = status


class ImageFormatError(Exception):
    pass


class ImageFormatNotSupportedException(Exception):
    pass


class NotImplementedException(Exception):
    pass

