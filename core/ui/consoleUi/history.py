import copy

class historyTable:
	def __init__(self):
		self._table = {}

	def getHistory(self, key):
		if self._table.has_key(key):
			result = self._table[key]
		else:
			result = history()
			self._table[key] = result

		return result

class history:

	def __init__(self):
		self._stack = []
		self._pointer = 0
		self._pending = None

	def remember(self, pending):
		self._stack.append(copy.deepcopy(pending))
		self._pointer = len(self._stack)
		

	def back(self, pending = None):
		if self._pointer == 0:
			return None

		if self._pointer == len(self._stack):
			self._pending = pending

		self._pointer -= 1
		return self._stack[self._pointer]

		
	def forward(self):
	
		sl = len(self._stack)
		if self._pointer == sl:
			return None

		self._pointer += 1

		if self._pointer == sl:
			if self._pending != None:
				result = self._pending
				self._pending = None
			else:
				result = None
		else:
			result = self._stack[self._pointer]
			
			
		return result
		
