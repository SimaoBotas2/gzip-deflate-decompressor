# Author: Marco Simoes
# Adapted from Java's implementation of Rui Pedro Paiva
# Teoria da Informacao, LEI, 2022

import sys
import numpy as np
from huffmantree import HuffmanTree


class GZIPHeader:
    ''' class for reading and storing GZIP header fields '''

    ID1 = ID2 = CM = FLG = XFL = OS = 0
    MTIME = []
    lenMTIME = 4
    mTime = 0

    # bits 0, 1, 2, 3 and 4, respectively (remaining 3 bits: reserved)
    FLG_FTEXT = FLG_FHCRC = FLG_FEXTRA = FLG_FNAME = FLG_FCOMMENT = 0

    # FLG_FTEXT --> ignored (usually 0)
    # if FLG_FEXTRA == 1
    XLEN, extraField = [], []
    lenXLEN = 2

    # if FLG_FNAME == 1
    fName = ''  # ends when a byte with value 0 is read

    # if FLG_FCOMMENT == 1
    fComment = ''   # ends when a byte with value 0 is read

    # if FLG_HCRC == 1
    HCRC = []

    def read(self, f):
        ''' reads and processes the Huffman header from file. Returns 0 if no error, -1 otherwise '''

        # ID 1 and 2: fixed values
        self.ID1 = f.read(1)[0]
        if self.ID1 != 0x1f:
            return -1  # error in the header

        self.ID2 = f.read(1)[0]
        if self.ID2 != 0x8b:
            return -1  # error in the header

            # CM - Compression Method: must be the value 8 for deflate
        self.CM = f.read(1)[0]
        if self.CM != 0x08:
            return -1  # error in the header

            # Flags
        self.FLG = f.read(1)[0]

        # MTIME
        self.MTIME = [0]*self.lenMTIME
        self.mTime = 0
        for i in range(self.lenMTIME):
            self.MTIME[i] = f.read(1)[0]
            self.mTime += self.MTIME[i] << (8 * i)

            # XFL (not processed...)
        self.XFL = f.read(1)[0]

        # OS (not processed...)
        self.OS = f.read(1)[0]

        # --- Check Flags
        self.FLG_FTEXT = self.FLG & 0x01
        self.FLG_FHCRC = (self.FLG & 0x02) >> 1
        self.FLG_FEXTRA = (self.FLG & 0x04) >> 2
        self.FLG_FNAME = (self.FLG & 0x08) >> 3
        self.FLG_FCOMMENT = (self.FLG & 0x10) >> 4

        # FLG_EXTRA
        if self.FLG_FEXTRA == 1:
            # read 2 bytes XLEN + XLEN bytes de extra field
            # 1st byte: LSB, 2nd: MSB
            self.XLEN = [0]*self.lenXLEN
            self.XLEN[0] = f.read(1)[0]
            self.XLEN[1] = f.read(1)[0]
            self.xlen = self.XLEN[1] << 8 + self.XLEN[0]

            # read extraField and ignore its values
            self.extraField = f.read(self.xlen)

        def read_str_until_0(f):
            s = ''
            while True:
                c = f.read(1)[0]
                if c == 0:
                    return s
                s += chr(c)

                # FLG_FNAME
        if self.FLG_FNAME == 1:
            self.fName = read_str_until_0(f)

            # FLG_FCOMMENT
        if self.FLG_FCOMMENT == 1:
            self.fComment = read_str_until_0(f)

            # FLG_FHCRC (not processed...)
        if self.FLG_FHCRC == 1:
            self.HCRC = f.read(2)

        return 0


class GZIP:
    ''' class for GZIP decompressing file (if compressed with deflate) '''

    gzh = None
    gzFile = ''
    fileSize = origFileSize = -1
    numBlocks = 0
    f = None

    bits_buffer = 0
    available_bits = 0

    def __init__(self, filename):
        self.gzFile = filename
        self.f = open(filename, 'rb')
        self.f.seek(0, 2)
        self.fileSize = self.f.tell()
        self.f.seek(0)

    def decompress(self):
        ''' main function for decompressing the gzip file with deflate algorithm '''

        numBlocks = 0

        # get original file size: size of file before compression
        origFileSize = self.getOrigFileSize()
        print(origFileSize)

        # read GZIP header
        error = self.getHeader()
        if error != 0:
            print('Formato invalido!')
            return

            # show filename read from GZIP header
        print(self.gzh.fName)
        outf = open(self.gzh.fName, "wb")

        # MAIN LOOP - decode block by block
        BFINAL = 0
        previousBuffer = []
        while not BFINAL == 1:

            BFINAL = self.readBits(1)
            #print(BFINAL)

            BTYPE = self.readBits(2)
            # print(BTYPE)
            if BTYPE != 2:
                print('Error: Block %d not coded with Huffman Dynamic coding' %
                      (numBlocks+1))
                return

                # --- STUDENTS --- ADD CODE HERE
            correctOrder = np.array([16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15])
            HLIT = self.readBits(5)
            HDIST = self.readBits(5)
            hclen = self.readBits(4)
            
            # Exercise 2
            alphCompCodigos = np.zeros(len(correctOrder), dtype=int)
            for i in range(hclen+4):
                alphCompCodigos[correctOrder[i]] = self.readBits(3)
            #print(alphCompCodigos)
            
            
            # Exercise 3
            
            hft = self.treeDecompress(alphCompCodigos)
            # create tree with the values, dont know what happens with empty string, need to test
            
            HLITArray = np.zeros(HLIT + 257, dtype=int)  # create array for exercise 4
            HDISTArray = np.zeros(HDIST + 1, dtype=int)  # create array for exercise 5
            i = 0

            while(i < len(HLITArray)):
                read = str(self.readBits(1))
                TreePosition = hft.nextNode(read)

                if TreePosition == -1:
                    print("Error reading the Tree")
                    break
    
                if TreePosition == -2:
                    continue
        
                if TreePosition in (16, 17, 18):
                    bitrepetition = 3 + self.readBits(2) if TreePosition == 16 else (
                        3 + self.readBits(3) if TreePosition == 17 else 11 + self.readBits(7)
                    )
                    k = 0
                    while k < bitrepetition:
                        HLITArray[i + k] = HLITArray[i - 1] if TreePosition == 16 else 0
                        k += 1
                    i += k
                    k = 0
                    hft.resetCurNode()
         
                if TreePosition < 16:
                    HLITArray[i] = TreePosition
                    i += 1
                    hft.resetCurNode()

            #print(HLITArray)
            i = 0
            while(i < len(HDISTArray)):
                read = str(self.readBits(1))
                TreePosition = hft.nextNode(read)
                    
                if TreePosition == -1:
                    print("Error reading the Tree")
                    break
    
                if TreePosition == -2:
                    continue
        
                if TreePosition in (16, 17, 18):
                    bitrepetition = 3 + self.readBits(2) if TreePosition == 16 else (
                        3 + self.readBits(3) if TreePosition == 17 else 11 + self.readBits(7)
                    )
                    k = 0
                    while k < bitrepetition:
                        HDISTArray[i + k] = HDISTArray[i - 1] if TreePosition == 16 else 0
                        k += 1
                    i += k
                    k = 0
                    hft.resetCurNode()
         
                if TreePosition < 16:
                    HDISTArray[i] = TreePosition
                    i += 1
                    hft.resetCurNode()

           #print(HDISTArray)
            
            
            #Exercise 6
            
           # print("EX 6")
            
            # HLITArray
            HLIThuffmanTree = self.treeDecompress(HLITArray)
            #print(HLIThuffmanTree)
            
            # HDISTArray
            HDISThuffmanTree = self.treeDecompress(HDISTArray)
            #print(HDISThuffmanTree)


            #Exercise 7
            
            outBuffer = [] * 32768
            TreePosition =-2
            i=0
            while(TreePosition !=256):
                read = str(self.readBits(1))
                TreePosition = HLIThuffmanTree.nextNode(read)
                
                if TreePosition == -1:
                    print("Error reading the Tree")
                    break
    
                if TreePosition == -2:
                    continue
                
                if(TreePosition<256):
                    outBuffer.insert(i,TreePosition)
                    i+=1
                    lenght = 0
                
                elif (TreePosition>=257 and TreePosition<=264):
                    lenght = (TreePosition - 257) + 3
                
                elif(TreePosition >= 265 and TreePosition <= 284):
                    lenght = self.getLenght(TreePosition, int((TreePosition-257)/4))
                
                elif(TreePosition == 285):
                    lenght = 258
                    
                elif(TreePosition == 256):
                    break
                    
                if(lenght>0):
                    distance = self.runDistTree(HDISThuffmanTree)
                    aux = len(outBuffer) - distance
                    for x in range(lenght):
                        if(aux>=0):
                            outBuffer.insert(i,outBuffer[aux])
                        else:
                            outBuffer.insert(i,previousBuffer[aux])
                        aux+=1
                        i+=1
                        
                HLIThuffmanTree.resetCurNode()
                    
            #escrever no ficheiro o buffer 
            outf.write(bytearray(outBuffer))
            previousBuffer = outBuffer
            
            # update number of blocks read
            numBlocks += 1
            print("updating number of blocks " + str(numBlocks)) 
            # Close file
        outf.close

        self.f.close()
        print("End: %d block(s) analyzed." % numBlocks)
        
    def treeDecompress(self, CompressedTree):
        ArrayCopy = np.copy(CompressedTree)
        ArrayCopy = np.where( ArrayCopy == 0, 99, ArrayCopy)
        decodedValues = np.zeros_like(ArrayCopy)
        minimum = 0
        aux = -1
        # print(ArrayCopy)
        while ArrayCopy.min() < 99:
            aux = (aux+1) * (2**(ArrayCopy.min() - minimum))
            minimum = ArrayCopy.min()
            decodedValues[ArrayCopy.argmin()] = aux
            ArrayCopy[ArrayCopy.argmin()] = 99
            # print(aux)
        
        # print(decodedValues)
        
        decodedValuesBin = [];
        for i in range(len(decodedValues)):
            valueToDecode = decodedValues[i]
            binaryNumber = np.zeros(CompressedTree[i], dtype=int)
            for k in range(CompressedTree[i]):
                bit = valueToDecode & 1
                binaryNumber[-(k+1)] = bit  # so it starts in the end to the beggining of the string
                valueToDecode = valueToDecode >> 1
            decodedValuesBin.append(binaryNumber.tolist())
        # print(str(decodedBinary)) #decodedBinary

        decodedBinaryStringArray = np.array([''.join(map(str, x))for x in decodedValuesBin], dtype=object)
       # print (decodedBinaryStringArray)

        hft = HuffmanTree()
        # create tree with the values, dont know what happens with empty string, need to test
        for i in range(len(decodedBinaryStringArray)):
            if(len(decodedBinaryStringArray[i]) > 0):
                error = hft.addNode(decodedBinaryStringArray[i], i)  # add third parameter as true to print the nodes insertion
        
        return hft

    def getLenght(self, TreePosition, specialKey):
        return ((TreePosition - (specialKey*4 + 257))*(2**(specialKey-1)) + (2**(specialKey+1)) + 3) + self.readBits(specialKey-1)

    def runDistTree(self,DistanceTree):
        
        distance = 0
        TreePosition=-2
        
        while(TreePosition==-2):
            read = str(self.readBits(1))
            TreePosition = DistanceTree.nextNode(read)
            
            if TreePosition == -1:
                print("Error reading the Tree")
                break
            if TreePosition == -2:
                continue
            
            
        if(TreePosition >= 0 and TreePosition<= 3):
            distance = TreePosition + 1
            
        elif(TreePosition > 3 and TreePosition < 30):
            distance = self.findDistance(int(TreePosition/2), TreePosition)
            
            
        DistanceTree.resetCurNode()
        return distance


    def findDistance(self, specialKey, TreePosition):
        return (TreePosition - specialKey*2)*(2**(specialKey-1)) + (2**(specialKey)+1) + self.readBits(specialKey-1)

    def getOrigFileSize(self):
        ''' reads file size of original file (before compression) - ISIZE '''

        # saves current position of file pointer
        fp = self.f.tell()

        # jumps to end-4 position
        self.f.seek(self.fileSize-4)

        # reads the last 4 bytes (LITTLE ENDIAN)
        sz = 0
        for i in range(4):
            sz += self.f.read(1)[0] << (8*i)

            # restores file pointer to its original position
        self.f.seek(fp)

        return sz

    def getHeader(self):
        ''' reads GZIP header'''

        self.gzh = GZIPHeader()
        header_error = self.gzh.read(self.f)
        return header_error

    def readBits(self, n, keep=False):
        ''' reads n bits from bits_buffer. if keep = True, leaves bits in the buffer for future accesses '''

        while n > self.available_bits:
            self.bits_buffer = self.f.read(
                1)[0] << self.available_bits | self.bits_buffer
            self.available_bits += 8

        mask = (2**n)-1
        value = self.bits_buffer & mask

        if not keep:
            self.bits_buffer >>= n
            self.available_bits -= n

        return value


if __name__ == '__main__':

    # gets filename from command line if provided
    fileName = "FAQ.txt.gz"
    if len(sys.argv) > 1:
        fileName = sys.argv[1]

        # decompress file
    gz = GZIP(fileName)
    gz.decompress()
