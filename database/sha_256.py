import numpy as np
from collections import deque



class Hash:
	def __init__(self, inp):
	    self.input = inp
	    self.curr = []
	    self.curr_str = ""

	    self.h0 = 0x6a09e667
	    self.h1 = 0xbb67ae85
	    self.h2 = 0x3c6ef372
	    self.h3 = 0xa54ff53a
	    self.h4 = 0x510e527f
	    self.h5 = 0x9b05688c
	    self.h6 = 0x1f83d9ab
	    self.h7 = 0x5be0cd19

	    self.k = [0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
	         0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
	         0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
	         0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
	         0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
	         0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
	         0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
	         0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2]


	def split_data(self, string, n):
	  	temp = ""
	  	l = []
	  	for count, i in enumerate(string+"0"):
	  		if count % n == 0 and count != 0:
	  			l.append(temp)
	  			temp = ""
	  		temp += i

	  	return l


	def pre_processing(self):
	    self.curr = ["0"+str(bin(i)[2:]) if len(bin(i)[2:]) == 7 else "00"+str(bin(i)[2:]) for i in [ord(x) for x in self.input]]
	    big_endian = bin(len("".join(self.curr))).replace("0b", "")

	    self.curr.append("1")

	    self.curr_str = "".join(self.curr) 
	    self.curr = []

	    while len(self.curr_str) % 512 != 0:
	      self.curr_str += "0"  
	    self.curr_str = self.curr_str[:-64]

	    self.curr_str += "0"*(64-len(big_endian))
	    self.curr_str += big_endian
	    self.curr = self.split_data(self.curr_str, 8)

	    return self.curr


	def right_rotate(self, bits, n):
		deque_ = deque([i for i in bits])
		deque_.rotate(n)

		return "".join(list(deque_))

	def right_shift(self, bits, n):
		s = bin( int(bits, 2) >>  n ).replace("0b","")
		s = (32-len(s))*"0" + s

		return s


	def xor(self, b1, b2):
		x = bin( int(b1, 2) ^ int(b2, 2)).replace("0b","")
		x = (32-len(x))*"0" + x

		return x

	def and_(self, b1, b2):
		x = bin(int(b1, 2) & int(b2, 2)).replace("0b","")
		x = (32-len(x))*"0" + x

		return x

	def not_(self, b1):
		x = bin(~int(b1, 2)).replace("0b","")
		x = x.replace("-","")
		x = (32-len(x))*"0" + x
		return x

	def mod_addition(self, elements):
		sum_ = sum([int(i, 2) for i in elements])
		if sum_ > 2**32:
			sum_ = sum_ % (2**32)

		sum_ = bin(sum_).replace("0b", "")
		sum_ = (32-len(sum_))*"0" + sum_

		return sum_
	
	def message_schedule(self):
		self.curr_str += "0"*(48*32)
		self.curr = self.split_data(self.curr_str, 32)

		s0 = s1 = ""


		for i in range(16, 63):
			s0 = self.xor( self.xor((self.right_rotate(self.curr[i-15], 7)), (self.right_rotate(self.curr[i-15], 18))), self.right_shift(self.curr[i-15], 3) )
			s1 = self.xor( self.xor((self.right_rotate(self.curr[i-2], 17)), (self.right_rotate(self.curr[i-2], 19))), self.right_shift(self.curr[i-2], 10) )
			self.curr[i] = self.mod_addition([self.curr[i-16], s0, self.curr[i-7], s1])

		return self.curr, len(self.curr)

	def compression(self):
		a = bin(self.h0).replace("0b", "0")
		b = bin(self.h1).replace("0b", "0")
		c = bin(self.h2).replace("0b", "0")
		d = bin(self.h3).replace("0b", "0")
		e = bin(self.h4).replace("0b", "0")
		f = bin(self.h5).replace("0b", "0")
		g = bin(self.h6).replace("0b", "0")
		h = bin(self.h7).replace("0b", "0")

		s0 = s1 = temp1 = temp2 = ch = maj = ""

		for i in range(0, 63):
			s1 = self.xor( self.xor( self.right_rotate(e, 6), self.right_rotate(e, 11) ), self.right_rotate(e, 25) )
			ch = self.xor((self.and_(e, f)), (self.and_(self.not_(e), g)))
			temp1 = self.mod_addition([h, s1, ch, bin(self.k[i]).replace("0b", "0"), self.curr[i]])

			s0 = self.xor( self.xor( self.right_rotate(a, 2), self.right_rotate(a, 13) ), self.right_rotate(a, 22) )
			maj = self.xor( self.xor((self.and_(a, b)), (self.and_(a, c))), self.and_(b, c))
			temp2 = self.mod_addition([s0, maj])

			h = g
			g = f
			f = e
			e = self.mod_addition([d, temp1])
			d = c
			c = b
			b = a
			a = self.mod_addition([temp1, temp2])

		self.h0 = self.mod_addition([bin(self.h0).replace("0b", "0"), a])
		self.h1 = self.mod_addition([bin(self.h1).replace("0b", "0"), b])
		self.h2 = self.mod_addition([bin(self.h2).replace("0b", "0"), c])
		self.h3 = self.mod_addition([bin(self.h3).replace("0b", "0"), d])
		self.h4 = self.mod_addition([bin(self.h4).replace("0b", "0"), e])
		self.h5 = self.mod_addition([bin(self.h5).replace("0b", "0"), f])
		self.h6 = self.mod_addition([bin(self.h6).replace("0b", "0"), g])
		self.h7 = self.mod_addition([bin(self.h7).replace("0b", "0"), h])

		digest = hex(int(self.h0+self.h1+self.h2+self.h3+self.h4+self.h5+self.h6+self.h7, 2))

		return digest





      
h = Hash("Paponne")
h.pre_processing()
h.message_schedule()
print(h.compression())










import hashlib

def sha256_1(data):
    m = hashlib.sha256()
    m.update(data.encode())
    return m.hexdigest()

#print(sha256_1("hello world"))
