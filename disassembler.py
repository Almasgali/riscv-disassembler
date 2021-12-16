import sys


class Symbol:

    def __init__(self, start):
        self.name = get32bit(start)
        self.strtab_name = ""
        if self.name != 0:
            j = 0
            while byte[strtab.offset + self.name + j] != 0:
                self.strtab_name += chr(byte[strtab.offset + self.name + j])
                j += 1
        self.value = get32bit(start + 4)
        self.size = get32bit(start + 8)
        self.info = byte[start + 12]
        self.bind = self.info >> 4
        self.type = self.info & 0xf
        self.other = byte[start + 13]
        self.vis = self.other & 0x3
        self.shndx = get16bit(start + 14)

    def __str__(self):
        return ("name: " + str(self.strtab_name) + " value: " + str(self.value)
                + " size: " + str(self.size) + " bind: " + str(self.bind) + " type: " + str(self.type))


class Section:

    def __init__(self, index):
        self.name = get32bit(e_shoff + 40 * index)
        self.type = get32bit(e_shoff + 40 * index + 4)
        self.addres = get32bit(e_shoff + 40 * index + 12)
        self.offset = get32bit(e_shoff + 40 * index + 16)
        self.size = get32bit(e_shoff + 40 * index + 20)
        self.entsize = get32bit(e_shoff + 40 * index + 36)

    def __str__(self):
        return ("name: " + str(self.name) + " type: " + str(self.type)
                + " offset: " + str(self.offset) + " size: " + str(self.size)
                + " entsize: " + str(self.entsize))


# func to get 4 - bite little endian number
def get32bit(start):
    return byte[start] | byte[start + 1] << 8 | byte[start + 2] << 16 | byte[start + 3] << 24


# func to get 2 - bite little endian number
def get16bit(start):
    return byte[start] | byte[start + 1] << 8


# func to get sign-extended number
def bin2int(x):
    res = int(x, 2)
    if x[0] == '1':
        res -= 2 ** len(x)
    return str(res)


try:
    inp = open(sys.argv[1], "rb")
except:
    print("Error: can't open input file.")
    quit()

try:
    out = open(sys.argv[2], "w")
except:
    print("Error: can't open output file.")
    quit()

byte = inp.read()

# reading header

if not (byte[0] == 0x7f and byte[1] == 0x45 and byte[2] == 0x4c and byte[3] == 0x46):
    print("Error: input is not an elf - file.")
    quit()

if not (byte[4] == 1):
    print("Error: input is not a 32 - bit file.")
    quit()

if not (byte[5] == 1):
    print("Error: input is not in a Little Endian.")
    quit()

if not (get32bit(20) == 1):
    print("Error: input file has incorrect version")
    quit()

e_shoff = get32bit(32)
e_shnum = get16bit(48)

# reading sections info

sections = []

for i in range(e_shnum):
    sections.append(Section(i))

for section in sections:
    if section.type == 3:
        name = ""
        ind = 0
        while byte[section.offset + section.name + ind] != 0:
            name += chr(byte[section.offset + section.name + ind])
            ind += 1
        if name == ".shstrtab":
            shstrtab = section

# parsing .symtab section

for section in sections:
    if section.type == 2:
        symtab = section
    if section.type == 3:
        name = ""
        ind = 0
        while byte[shstrtab.offset + section.name + ind] != 0:
            name += chr(byte[shstrtab.offset + section.name + ind])
            ind += 1
        if name == ".strtab":
            strtab = section

symbols = []

for i in range(symtab.size // symtab.entsize):
    symbols.append(Symbol(symtab.offset + symtab.entsize * i))

labels = dict()
for symbol in symbols:
    if symbol.strtab_name != "":
        labels[symbol.value] = symbol.strtab_name

# parsing .text section

for section in sections:
    if (section.type == 1):
        name = ""
        ind = 0
        while byte[shstrtab.offset + section.name + ind] != 0:
            name += chr(byte[shstrtab.offset + section.name + ind])
            ind += 1
        if name == ".text":
            progbits = section

registers = {"00000": "zero", "00001": "ra",
             "00010": "sp", "00011": "gp",
             "00100": "tp", "00101": "t0",
             "00110": "t1", "00111": "t2",
             "01000": "s0", "01001": "s1",
             "01010": "a0", "01011": "a1",
             "01100": "a2", "01101": "a3",
             "01110": "a4", "01111": "a5",
             "10000": "a6", "10001": "a7",
             "10010": "s2", "10011": "s3",
             "10100": "s4", "10101": "s5",
             "10110": "s6", "10111": "s7",
             "11000": "s8", "11001": "s9",
             "11010": "s10", "11011": "s11",
             "11100": "t3", "11101": "t4",
             "11110": "t5", "11111": "t6", }

rvc_registers = {"000": "s0", "001": "s1",
                 "010": "a0", "011": "a1",
                 "100": "a2", "101": "a3",
                 "110": "a4", "111": "a5"}

labelInd = 0
to_out = []  # list of what we are going to write in output file


def parse_rvc():
    global labelInd
    cur_cmd = bin(get16bit(offs))[2:]
    while len(cur_cmd) != 16:
        cur_cmd = '0' + cur_cmd
    buf = ['0' * (8 - len(addr)) + addr, "", "", "", ""]
    if int(cur_cmd, 2) == 0:
        to_out.append(buf)
        return
    if int(cur_cmd, 2) == 1:
        buf[2] = "c.nop"
        to_out.append(buf)
        return
    if cur_cmd == '1001000000000010':
        buf[2] = "c.ebreak"
        to_out.append(buf)
        return
    opcode = cur_cmd[14:]
    funct = cur_cmd[:3]
    if opcode == '10':
        rd = cur_cmd[4:9]
        if funct == '000':
            if int(rd, 2) == 0 or int(cmd[3] + cmd[9:14], 2) == '0':
                buf[2] = 'c.nop'
            else:
                buf[2] = 'c.slli'
                buf[3] = registers[rd]
                buf[4] = bin2int(cmd[3] + cmd[9:14])
        elif funct == '001':
            buf[2] = 'c.fldsp'
            buf[3] = registers[rd]
            buf[4] = int(cur_cmd[11:14] + cur_cmd[3] + cur_cmd[9:11] + '000', 2)
            buf.append("sp")
        elif funct == '010' and int(rd, 2) != 0:
            buf[2] = 'c.lwsp'
            buf[3] = registers[rd]
            buf[4] = int(cur_cmd[12:14] + cur_cmd[3] + cur_cmd[9:12] + '00', 2)
            buf.append("sp")
        elif funct == '011':
            buf[2] = 'c.flwsp'
            buf[3] = registers[rd]
            buf[4] = int()
            buf[4] = int(cur_cmd[12:14] + cur_cmd[3] + cur_cmd[9:12] + '00', 2)
            buf.append("sp")
        elif funct == '100':
            if cur_cmd[3] == '0' and rd != '00000' and cur_cmd[9:14] == '00000':
                buf[2] = 'c.jr'
                buf[3] = registers[rd]
            elif cur_cmd[3] == '0' and rd != '00000' and cur_cmd[9:14] != '00000':
                buf[2] = 'c.mv'
                buf[3] = registers[rd]
                buf[4] = registers[cur_cmd[9:14]]
            elif cur_cmd[3] == '1' and rd != '00000' and cur_cmd[9:14] == '00000':
                buf[2] = 'c.jalr'
                buf[3] = registers[rd]
            elif cur_cmd[3] == '1' and rd != '00000' and cur_cmd[9:14] != '00000':
                buf[2] = 'c.add'
                buf[3] = registers[rd]
                buf[4] = registers[cur_cmd[9:14]]
        elif funct == '101':
            buf[2] = 'c.fsdsp'
            buf[3] = registers[cur_cmd[9:14]]
            buf[4] = int(cur_cmd[6:9] + cur_cmd[3:6] + '000', 2)
            buf.append("sp")
        elif funct == '110':
            buf[2] = 'c.swsp'
            buf[3] = registers[cur_cmd[9:14]]
            buf[4] = int(cur_cmd[7:9] + cur_cmd[3:7] + '00', 2)
            buf.append("sp")
        elif funct == '111':
            buf[2] = 'c.fswsp'
            buf[3] = registers[cur_cmd[9:14]]
            buf[4] = int(cur_cmd[7:9] + cur_cmd[3:7] + '00', 2)
            buf.append("sp")
    elif opcode == '01':
        if funct == '000':
            buf[2] = 'c.addi'
            buf[3] = registers[cur_cmd[4:9]]
            buf[4] = bin2int(cur_cmd[3] + cur_cmd[9:14])
        elif funct == '001':
            buf[2] = 'c.jal'
            buf[3] = bin2int(cur_cmd[3] + cur_cmd[7] + cur_cmd[5:7] + cur_cmd[9] + cur_cmd[8]
                         + cur_cmd[13] + cur_cmd[4] + cur_cmd[10:13] + '0')
            if int(addr, 16) + int(buf[3]) in labels:
                buf[4] = labels[int(addr, 16) + int(buf[3])]
            else:
                labels[int(addr, 16) + int(buf[3])] = "LOC_%05x" % labelInd
                buf[4] = labels[int(addr, 16) + int(buf[3])]
                labelInd += 1
        elif funct == '010':
            buf[2] = 'c.li'
            buf[3] = registers[cur_cmd[4:9]]
            buf[4] = bin2int(cur_cmd[3] + cur_cmd[9:14])
        elif funct == '011':
            if int(cur_cmd[4:9], 2) == 2:
                buf[2] = 'c.addi116sp'
                buf[3] = 'sp'
                buf[4] = bin2int(cur_cmd[3] + cur_cmd[11:13] + cur_cmd[10] + cur_cmd[13] + cur_cmd[9] + '0000')
            else:
                buf[2] = 'c.lui'
                buf[3] = registers[cur_cmd[4:9]]
                buf[4] = bin2int(cur_cmd[3] + cur_cmd[9:14] + '0' * 12)
        elif funct == '100':
            opcode1 = cur_cmd[4:6]
            opcode2 = cur_cmd[9:11]
            rd = cur_cmd[6:9]
            rs2 = cur_cmd[11:14]
            if opcode1 == '10':
                buf[2] = 'c.andi'
                buf[3] = rvc_registers[rd]
                buf[4] = bin2int(cur_cmd[3] + cur_cmd[9:14])
            elif opcode1 == '11':
                if opcode2 == '00':
                    buf[2] = 'c.sub'
                elif opcode2 == '01':
                    buf[2] = 'c.xor'
                elif opcode2 == '10':
                    buf[2] = 'c.or'
                elif opcode2 == '11':
                    buf[2] = 'c.and'
                buf[3] = rvc_registers[rd]
                buf[4] = rvc_registers[rs2]
            elif opcode1 == '00':
                buf[2] = 'c.srli'
                buf[3] = rvc_registers[rd]
                buf[4] = int(cur_cmd[3] + cur_cmd[9:14], 2)
            elif opcode1 == '01':
                buf[2] = 'c.srai'
                buf[3] = rvc_registers[rd]
                buf[4] = int(cur_cmd[3] + cur_cmd[9:14], 2)

        elif funct == '101':
            buf[2] = 'c.j'
            buf[3] = int(cur_cmd[3] + cur_cmd[7] + cur_cmd[5:7] + cur_cmd[9] + cur_cmd[8]
                         + cur_cmd[13] + cur_cmd[4] + cur_cmd[10:13] + '0', 2)
            if int(addr, 16) + int(buf[3]) in labels:
                buf[4] = labels[int(addr, 16) + int(buf[3])]
            else:
                labels[int(addr, 16) + int(buf[3])] = "LOC_%05x" % labelInd
                buf[4] = labels[int(addr, 16) + int(buf[3])]
                labelInd += 1
        elif funct == '110':
            buf[2] = 'c.beqz'
            buf[3] = rvc_registers[cur_cmd[6:9]]
            buf[4] = bin2int(cur_cmd[3] + cur_cmd[9:11] + cur_cmd[13] + cur_cmd[4:6] + cur_cmd[11:13] + '0')
            buf.append("")
            if int(addr, 16) + int(buf[4]) in labels:
                buf[5] = labels[int(addr, 16) + int(buf[4])]
            else:
                labels[int(addr, 16) + int(buf[4])] = "LOC_%05x" % labelInd
                buf[5] = labels[int(addr, 16) + int(buf[4])]
                labelInd += 1
        elif funct == '111':
            buf[2] = 'c.bnez'
            buf[3] = rvc_registers[cur_cmd[6:9]]
            buf[4] = bin2int(cur_cmd[3] + cur_cmd[9:11] + cur_cmd[13] + cur_cmd[4:6] + cur_cmd[11:13] + '0')
            buf.append("")
            if int(addr, 16) + int(buf[4]) in labels:
                buf[5] = labels[int(addr, 16) + int(buf[4])]
            else:
                labels[int(addr, 16) + int(buf[4])] = "LOC_%05x" % labelInd
                buf[5] = labels[int(addr, 16) + int(buf[4])]
                labelInd += 1
    elif opcode == '00':
        rd = cur_cmd[11:14]
        rs1 = cur_cmd[6:9]
        funct = cur_cmd[:3]
        buf.append("")
        if funct == '000':
            buf[2] = 'c.addi4spn'
            buf[3] = rvc_registers[rd]
            buf[4] = 'sp'
            buf[5] = bin2int(cur_cmd[5:9] + cur_cmd[3:5] + cur_cmd[10] + cur_cmd[9] + '00')
        elif funct == '001':
            buf[2] = 'c.fld'
            buf[3] = rvc_registers[rd]
            buf[4] = int(cur_cmd[9:11] + cur_cmd[3:6] + '000', 2)
            buf[5] = rvc_registers[rs1]
        elif funct == '010':
            buf[2] = 'c.lw'
            buf[3] = rvc_registers[rd]
            buf[4] = int(cur_cmd[10] + cur_cmd[3:6] + cur_cmd[9] + '00', 2)
            buf[5] = rvc_registers[rs1]
        elif funct == '011':
            buf[2] = 'c.flw'
            buf[3] = rvc_registers[rd]
            buf[4] = int(cur_cmd[10] + cur_cmd[3:6] + cur_cmd[9] + '00', 2)
            buf[5] = rvc_registers[rs1]
        elif funct == '101':
            buf[2] = 'c.fsd'
            buf[3] = rvc_registers[rd]
            buf[4] = int(cur_cmd[9] + cur_cmd[10] + cur_cmd[3:6] + '000', 2)
            buf[5] = rvc_registers[rs1]
        elif funct == '110':
            buf[2] = 'c.sw'
            buf[3] = rvc_registers[rd]
            buf[4] = int(cur_cmd[10] + cur_cmd[3:6] + cur_cmd[9] + '00', 2)
            buf[5] = rvc_registers[rs1]
        elif funct == '111':
            buf[2] = 'c.fsw'
            buf[3] = rvc_registers[rd]
            buf[4] = int(cur_cmd[10] + cur_cmd[3:6] + cur_cmd[9] + '00', 2)
            buf[5] = rvc_registers[rs1]
    to_out.append(buf)


def parse_rv():
    global labelInd
    buf = ['0' * (8 - len(addr)) + addr, "", "", "", "", ""]
    opcode = cmd[25:]
    rd = cmd[20:25]
    rs1 = cmd[12:17]
    rs2 = cmd[7:12]
    funct3 = cmd[17:20]
    if opcode == '1110011':
        if cmd == '00000000000000000000000001110011':
            buf[2] = "ecall"
        elif cmd == '00000000000100000000000001110011':
            buf[2] = "ebreak"
        else:
            if funct3 == '001':
                buf[2] = 'csrrw'
            if funct3 == '010':
                buf[2] = 'csrrs'
            if funct3 == '011':
                buf[2] = 'csrrc'
            if funct3 == '101':
                buf[2] = 'csrrwi'
            if funct3 == '110':
                buf[2] = 'csrrsi'
            if funct3 == '111':
                buf[2] = 'csrrci'
            buf[3] = registers[rd]
            buf[4] = bin2int(cmd[:12])
            buf[4] = registers[rs1]
    elif opcode == '0110111':
        buf[2] = "lui"
        buf[3] = registers[rd]
        buf[4] = bin2int(cmd[:20])
    elif opcode == '0010111':
        buf[2] = "auipc"
        buf[3] = registers[rd]
        buf[4] = bin2int(cmd[:20])
    elif opcode == '1101111':
        buf[2] = "jal"
        buf[3] = registers[rd]
        buf[4] = bin2int(cmd[0] + cmd[12:20] + cmd[11] + cmd[1:11] + '0')
        if int(addr, 16) + int(buf[4]) in labels:
            buf[5] = labels[int(addr, 16) + int(buf[4])]
        else:
            labels[int(addr, 16) + int(buf[4])] = "LOC_%05x" % labelInd
            buf[5] = labels[int(addr, 16) + int(buf[4])]
            labelInd += 1
    elif opcode == '1100111':
        buf[2] = "jalr"
        buf[3] = registers[rd]
        buf[4] = bin2int(cmd[7:12])
        buf[5] = registers[rs1]
    elif opcode == '1100011':
        if funct3 == '000':
            buf[2] = "beq"
        if funct3 == '001':
            buf[2] = "bne"
        if funct3 == '100':
            buf[2] = "blt"
        if funct3 == '101':
            buf[2] = "bge"
        if funct3 == '110':
            buf[2] = "bltu"
        if funct3 == '111':
            buf[2] = "bgeu"
        buf[3] = registers[rs1]
        buf[4] = registers[rs2]
        buf[5] = bin2int(cmd[0] + cmd[24] + cmd[1:7] + cmd[20:24] + '0')
        buf.append("")
        if int(addr, 16) + int(buf[5]) in labels:
            buf[6] = labels[int(addr, 16) + int(buf[5])]
        else:
            labels[int(addr, 16) + int(buf[5])] = "LOC_%05x" % labelInd
            buf[6] = labels[int(addr, 16) + int(buf[5])]
            labelInd += 1
    elif opcode == '0010011':
        if cmd[:7] == '0000000':
            if funct3 == '001':
                buf[2] = 'slli'
                buf[3] = registers[rd]
                buf[4] = registers[rs1]
                buf[5] = int(rs2, 2)
            if funct3 == '101':
                buf[2] = 'srli'
                buf[3] = registers[rd]
                buf[4] = registers[rs1]
                buf[5] = int(rs2, 2)
        elif cmd[:7] == '0100000':
            if funct3 == '101':
                buf[2] = 'srai'
                buf[3] = registers[rd]
                buf[4] = registers[rs1]
                buf[5] = int(rs2, 2)
        if buf[2] == "":
            if funct3 == '000':
                buf[2] = "addi"
            if funct3 == '010':
                buf[2] = "slti"
            if funct3 == '011':
                buf[2] = "sltiu"
            if funct3 == '100':
                buf[2] = "xori"
            if funct3 == '110':
                buf[2] = "ori"
            if funct3 == '111':
                buf[2] = "andi"
            buf[3] = registers[rd]
            buf[4] = registers[rs1]
            buf[5] = bin2int(cmd[:12])
    elif opcode == '0000011':
        if funct3 == '000':
            buf[2] = "lb"
        if funct3 == '001':
            buf[2] = "lh"
        if funct3 == '010':
            buf[2] = "lw"
        if funct3 == '100':
            buf[2] = "lbu"
        if funct3 == '101':
            buf[2] = "lhu"
        buf[3] = registers[rd]
        buf[4] = bin2int(cmd[:12])
        buf[5] = registers[rs1]
    elif opcode == '0100011':
        if funct3 == '000':
            buf[2] = "sb"
        if funct3 == '001':
            buf[2] = "sh"
        if funct3 == '010':
            buf[2] = "sw"
        buf[3] = registers[cmd[7:12]]
        buf[4] = bin2int(cmd[:7] + cmd[20:25])
        buf[5] = registers[rs1]
    elif opcode == '0110011':
        if cmd[:7] == '0000001':
            if funct3 == '000':
                buf[2] = 'mul'
            if funct3 == '001':
                buf[2] = 'mulh'
            if funct3 == '010':
                buf[2] = 'mulhsu'
            if funct3 == '011':
                buf[2] = 'mulhu'
            if funct3 == '100':
                buf[2] = 'div'
            if funct3 == '101':
                buf[2] = 'divu'
            if funct3 == '110':
                buf[2] = 'rem'
            if funct3 == '111':
                buf[2] = 'remu'
        else:
            if funct3 == '000':
                if cmd[:7] == '0000000':
                    buf[2] = 'add'
                elif cmd[:7] == '0100000':
                    buf[2] = 'sub'
            if funct3 == '001' and cmd[:7] == '0000000':
                buf[2] = 'sll'
            if funct3 == '010' and cmd[:7] == '0000000':
                buf[2] = 'slt'
            if funct3 == '011' and cmd[:7] == '0000000':
                buf[2] = 'sltu'
            if funct3 == '100' and cmd[:7] == '0000000':
                buf[2] = 'xor'
            if funct3 == '101':
                if cmd[:7] == '0000000':
                    buf[2] = 'srl'
                elif cmd[:7] == '0100000':
                    buf[2] = 'sra'
            if funct3 == '110' and cmd[:7] == '0000000':
                buf[2] = 'or'
            if funct3 == '111' and cmd[:7] == '0000000':
                buf[2] = 'and'
        buf[3] = registers[rd]
        buf[4] = registers[rs1]
        buf[5] = registers[rs2]
    to_out.append(buf)


offs = progbits.offset
adr = progbits.addres
while offs < progbits.offset + progbits.size:
    cmd = bin(get32bit(offs))[2:]
    while len(cmd) != 32:
        cmd = '0' + cmd
    addr = hex(adr)[2:]
    parse_rv()
    sz = 4
    if to_out[-1][2] == "":
        del to_out[-1]
        parse_rvc()
        sz = 2
    adr += sz
    offs += sz

# writing .text section

out.write(".text\n")

load_store = ["lb", "lh", "lw", "lbu", "lhu", "sb", "sh", "sw", "jalr", "c.sw"
              "c.fswsp", "c.swsp", "c.fsdsp", "c.flwsp", "c.lwsp", "c.fsd", "c.fsw"
              "c.fldsp", "c.fld", "c.lw", "c.flw"]

for i in range(len(to_out)):
    if to_out[i][2] == "":
        out.write("Error: unknown command\n")
        continue
    while to_out[i][-1] == "":
        del to_out[i][-1]
    if int(to_out[i][0], 16) in labels:
        to_out[i][1] = labels[int(to_out[i][0], 16)]
    if to_out[i][1] != "":
        s = "%08s %10s: %s" + " %s," * (len(to_out[i]) - 4)
    else:
        s = "%08s %10s  %s" + " %s," * (len(to_out[i]) - 4)
    if to_out[i][2] in load_store and len(to_out[i]) > 3:
        s = s[:-1] + "(%s)\n"
    elif len(to_out[i]) > 3:
        s += " %s\n"
    else:
        s += "\n"
    out.write(s % tuple(to_out[i]))

out.write('\n')

# writing .symtab section

out.write(".symtab\n")

types = {0: "NOTYPE",
         1: "OBJECT",
         2: "FUNC",
         3: "SECTION",
         4: "FILE",
         5: "COMMON",
         6: "TLS"}

bindings = {0: "LOCAL",
            1: "GLOBAL",
            2: "WEAK"}

visibility = {0: "DEFAULT",
              1: "INTERNAL",
              2: "HIDDEN",
              3: "PROTECTED"}

index = {0: "UNDEF",
         0xfff1: "ABS",
         0xfff2: "COMMON"}

out.write('%s %-15s %7s %-8s %-8s %-8s %6s %s\n' % (
    'Symbol', 'Value', 'Size', 'Type', 'Bind', 'Vis', 'Index', 'Name'))

for i in range(len(symbols)):

    if symbols[i].shndx in index:
        ind = index[symbols[i].shndx]
    elif 0xfff3 <= symbols[i].shndx <= 0xffff:
        ind = "RESERVE"
    elif 0xff00 <= symbols[i].shndx <= 0xff1f:
        ind = "PROC"
    else:
        ind = symbols[i].shndx

    if symbols[i].bind in bindings:
        bind = bindings[symbols[i].bind]
    elif 10 <= symbols[i].bind <= 12:
        bind = "OS"
    elif 13 <= symbols[i].bind <= 15:
        bind = "PROC"
    else:
        bind = "ERROR"

    if symbols[i].type in types:
        type = types[symbols[i].type]
    elif 10 <= symbols[i].type <= 12:
        type = "OS"
    elif 13 <= symbols[i].type <= 15:
        type = "PROC"
    else:
        type = "ERROR"

    out.write('[%4i] %-15s %5i %-8s %-8s %-8s %6s %s\n' % (
        i,
        hex(symbols[i].value),
        symbols[i].size,
        type,
        bind,
        visibility[symbols[i].vis],
        ind,
        symbols[i].strtab_name
    ))

inp.close()
out.close()