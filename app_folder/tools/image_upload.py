from cloudinary import uploader


def image_upload(image_str) -> str:
    result = uploader.upload(image_str)
    return result['url']