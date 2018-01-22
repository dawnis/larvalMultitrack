"""Functions associated with I/O"""
import cPickle

def writeTxtData(trackDict,data_file):
    """formats and writes the the data in trackDict to a text file in the following format:
    0x \t 0y \t 1x \t 1y \t ...\n
    x  \t y \t  x \t  y \t ... \n """
    f2write = open(data_file,'w')
    trackIDs = trackDict.keys()
    header_str = "".join(["%sx\t%sy\t"%(ID,ID) for ID in trackIDs])
    f2write.write(header_str[0:-1]+"\n")
    #ExtDataList = [cData for cData in trackDict.itervalues()]
    #dTable = np.concatenate(tuple(ExtDataList),axis=1)
    #np.savetxt(data_file,dTable,fmt="%2.2f", delimiter="\t", header=header_str)
    for row in range(9000):
        row_str = "".join(["%2.2f\t%2.2f\t"%(c[row,0],c[row,1]) for c in trackDict.itervalues()])
        f2write.write(row_str[0:-1]+"\n")
    f2write.close()

