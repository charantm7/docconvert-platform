class LibreOfficeNotFoundError(Exception):
    pass

class FileNotFoundError(Exception):
    pass

class ConversionTimeoutError(Exception):
    pass


class ConversionFailedError(Exception):
    pass

class UploadFailedError(Exception):
    pass

class CompressionFailedError(Exception):
    pass