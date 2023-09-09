
"""
BMS message en/descrambling for Offgridtec LiFePo4 Smart Pro Batteries
Note: only works for batteries with serial number "Bxxxxx"
      currently limited to 1 type of battery, _CRYPT string depends on serial number!
"""
__author__ = "patman15"
__license__ = "LGPL"

class OgtResp:
  #            00  01  02  03  04  05  06  07  08  09  10  11  12  13  14  15  
  _CRYPT = b'\x29\x28\x2B\x2A\x2D\x2C\x2F\x2E\x21\x20\x58\x5B\x5A\x5D\x5C\x5F'
  _TABDEC = bytearray.maketrans(_CRYPT, bytes(range(16)))
  _TABENC = bytearray.maketrans(bytes(range(16)), _CRYPT)
  
  def __init__(self,
               head: bytearray = bytearray(bytes(4)),
               reg: bytearray = bytearray(bytes(2)),
               value: bytearray = bytearray(bytes(6)),
               tail: bytearray = bytearray(bytes(2))
               ):
    self.head = head
    self.reg = reg
    self.value = value # can be 2, 4, or 6 long
    self.tail = tail
  
  @property
  def valid(self):
    return self.tail == bytearray(b'\x14\x13')

  @classmethod 
  def from_bytearray(self, resp: bytearray):
    return self(resp[0:4],
                self.to_int(resp[4:6]),
                self.to_int(resp[6:-2]),
                resp[-2:])

  @classmethod
  def to_int(self, value: bytearray) -> int:
    #print("\tval: ", value.hex())
    dec = value.translate(self._TABDEC)
    #print("\tdec: ", dec.hex())
    ret = bytearray((((dec[x] & 0xF) << 4) | (dec[x+1] & 0xF)) for x in range(0, len(dec), 2))
    #print("\tret: ", ret.hex())    
    return int.from_bytes(ret, byteorder='little')
  
  @classmethod
  def from_int(self, value: int) -> bytearray:
    #print("\tvalue: ", value)
    val = bytearray(value.to_bytes((value.bit_length()+7)//8, byteorder='big'))
    #print("\tval: ", val)
    ret = list()
    for x in range(0, len(val)):
      ret.insert(0,val[x] & 0xF)
      ret.insert(0,val[x] >> 4)
    #print("\tval: ", ret)
    return bytearray(ret).translate(self._TABENC)
    
  def show(self):
    print("header: ", self.head.hex(), 
          "register: ", self.reg, 
          "value: ", self.value,
          "tail: ", self.tail.hex())

def main():
#  resp = OgtResp.from_bytearray(bytearray(b'\x32\x4b\x5d\x35\x29\x5d\x2c\x20\x14\x13'))
#  resp = OgtResp.from_bytearray(bytearray(b'\x32\x4b\x5d\x35\x29\x20\x5D\x5D\x2A\x2A\x14\x13'))
#  resp = OgtResp.from_bytearray(bytearray(b'\x32\x4b\x5d\x35\x28\x21\x2d\x2a\x29\x2e\x29\x58\x14\x13')) # 18Ah
#  resp = OgtResp.from_bytearray(bytearray(b'\x32\x4b\x5d\x35\x28\x21\x2e\x5a\x28\x2e\x14\x13')) #  60AH
#  resp = OgtResp.from_bytearray(bytearray(b'\x32\x4b\x5d\x35\x29\x21\x28\x21\x14\x13'))  #20.2°C
#  resp = OgtResp.from_bytearray(bytearray(b'\x32\x4b\x5d\x35\x29\x5f\x2b\x5f\x29\x21\x29\x58\x14\x13'))  # Capacity (20AH)
#  resp = OgtResp.from_bytearray(bytearray(b'\x32\x4b\x5d\x35\x29\x58\x29\x29\x29\x29\x29\x58\x14\x13'))  # Current (0A)
#  resp = OgtResp.from_bytearray(bytearray(b'\x32\x4b\x5d\x35\x29\x58\x29\x2a\x29\x28\x29\x58\x14\x13'))  # Current (2.59A)
#  resp = OgtResp.from_bytearray(bytearray(b'\x32\x4b\x5d\x35\x29\x58\x5c\x5a\x5f\x5f\x14\x13'))  # Current (-0.19)
  resp = OgtResp.from_bytearray(bytearray(b'\x32\x4b\x5d\x35\x28\x5b\x2f\x58\x2c\x2d\x14\x13'))  # 
  print(resp.valid)

  resp.show()
  print(resp.value & 0x00FFFF)
  print(OgtResp.from_int(89).hex())
  print(OgtResp.from_int(13277).hex())
  print(OgtResp.from_int(6012).hex())

if __name__ == '__main__':
    main()
