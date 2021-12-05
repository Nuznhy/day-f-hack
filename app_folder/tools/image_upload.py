from cloudinary import uploader


def image_upload(image_str) -> str:
    try:
        result = uploader.upload(image_str)
    except FileNotFoundError as e:
        raise ValueError(e)
    return result['url']