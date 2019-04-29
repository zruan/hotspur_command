import hotspur_setup
from threading import Lock


class ResourceManager():

	gpu_locks = [(gpu_number, Lock()) for gpu_number in hotspur_setup.available_gpus]
	cpu_lock = Lock()
	available_cpus = hotspur_setup.available_cpus

	@classmethod
	def request_gpus(cls, number):
		gpu_id_list = []
		for gpu in cls.gpu_locks:
			if gpu[1].acquire(False):
				gpu_id_list.append(gpu[0])
				if len(gpu_id_list) == number:
					return gpu_id_list

		cls.release_gpus(gpu_id_list)
		return None
	
	@classmethod
	def release_gpus(cls, gpu_id_list):
		locks = [gpu[1] for gpu in cls.gpu_locks if gpu[0] in gpu_id_list]
		for lock in locks:
			lock.release()

	@classmethod
	def request_cpus(cls, number):
		cls.cpu_lock.acquire()
		success = False
		if cls.available_cpus >= number:
			cls.available_cpus -= number
			success = True
		cls.cpu_lock.release()
		return success

	@classmethod
	def release_cpus(cls, number):
		cls.cpu_lock.acquire()
		cls.available_cpus += number
		cls.cpu_lock.release()