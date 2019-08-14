import sys
import subprocess
from os import path

def get_frame_dose(image_path):
	command = [
		'clip',
		'stats',
		'-2d',
		'-iz',
		'1',
		image_path
		]
	process = subprocess.Popen(command, stdout=subprocess.PIPE)
	out, err = process.communicate()
	lines = out.split('\n')
	frame_dose = lines[2].split()[7]
	return frame_dose

def extract_from_file(file_path):
	ext = path.splitext(file_path)
	if ext == 'mdoc':
		return extract_from_mdoc
	if ext == 'xml':
		print("Cannot currently parse EPU XML data files.")
		sys.exit()

def extract_from_mdoc(mdoc_file_path):
	params = {}
	with open(mdoc_file_path, 'r') as mdoc:
		for line in mdoc.readlines():
			# key-value pairs are separated by ' = ' in mdoc files
			if not ' = ' in line:
				continue

			try:
				key, value = [item.strip() for item in line.split(' = ')]
				value_list = value.split(' ')
			except:
				continue

			if key == 'Voltage':
				params['voltage'] = int(value)
			elif key == 'ExposureDose':
				params['total_dose'] = float(value)
			elif key == 'ExposureTime':
				param['exposure_time'] = float(value)
			elif key == 'PixelSpacing':
				params['pixel_size'] = float(value)
			elif key == 'Binning':
				params['binning'] = float(value)
			elif key == 'NumSubFrames':
				params['frame_count'] = int(value)
			elif key == 'MinMaxMean':
				params['pixel_total_dose'] = float(value_list[2])
			elif key == 'DateTime':
				params['time'] = value
			elif key == 'FilterSlitAndLoss':
				params['filter_width'] = int(value_list[0])
				params['filter_loss'] = int(value_list[1])
			elif key == 'Magnification':
				params['nominal_magnification'] = value
			elif key == 'spot_size':
				params['spot_size'] = int(value)
			elif key == 'SubFramePath':
				params['image_path'] = os.path.absolute(os.path.value
	return params

def fill_in_dose_metrices(params):
	params.total_dose = params.frame_dose * params.frame_count


if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser("Parse mdoc for collection parameters and write to file.")
	parser.add_argument(
		'--mdoc-file',
		required=True,
		dest='mdoc_file',
		help='The modc file holding the collection parameters'
		)
	parser.add_argument(
		'--output-file',
		default='./collection_params.txt',
		dest='output_file',
		help='The file the extracted collection parameters will be written to.'
	)
	args = parser.parser_args()

	params_dict = extract_from_file(args.mdoc_file)
	params_dict.frame_pixel_dose = get_frame_dose(params_dict.image_path)
	params_dict = fill_in_dose_metrices(params_dict)

	print params_dict