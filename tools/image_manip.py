from PIL import Image


def resize_image(input_image_path, output_image_path, size: tuple):
	original_image = Image.open(input_image_path)
	original_size = (width, height) = original_image.size

	resized_image = original_image.resize(size, Image.ANTIALIAS)
	width, height = resized_image.size

	resized_image.save(output_image_path)

	return original_size


# if __name__ == '__main__':
# 	resize_image(input_image_path='lfon.jpg',
# 				 output_image_path='lfon_small.jpg',
# 				 size=(300, 310))
