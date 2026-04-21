from Crypto.Util.number import long_to_bytes, bytes_to_long

key = "0123456789012109876543210"
def encrypt(text):
  textnum = str(bytes_to_long(text.encode()))  
  if (len(str(textnum)) != 75):
    return "Huh? What's this number?"
  first_part = textnum[:25]
  second_part = textnum[25:50]
  third_part = textnum[50:75]

  blocknum = len(key)
  encrypted_first_part = ""
  encrypted_second_part = ""    
  encrypted_third_part = ""
  for i in range(blocknum):
      f = int(first_part[i])
      s = int(second_part[i])
      t = int(third_part[i])
      k = int(key[i])
      encrypted_f = format(((f | k) & (f ^ k)), 'x')
      encrypted_s = format(((s & k) ^ (s | k)), 'x')
      encrypted_t = format((t ^ ((t | k) & k)), 'x')
      encrypted_first_part += str(encrypted_f)
      encrypted_second_part += str(encrypted_s)
      encrypted_third_part += str(encrypted_t)

  encrypted_text = encrypted_first_part + encrypted_second_part + encrypted_third_part
  return encrypted_text

flag = "CPCTF{xxxxxxxxxxxxxxxxxxxxxxxx}"  #Can you determine it?

print(f"encrypted_flag : {encrypt(flag)}")
