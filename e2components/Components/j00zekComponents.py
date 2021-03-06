import inspect
from os import path, system

append2file=False
myDEBUG='/tmp/j00zekComponents.log'
imageType=None

def isImageType(imgName = ''):
	global imageType
	if imageType is None:
		if path.exists('/usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel'):
			imageType = 'vti'
		elif path.exists('/usr/lib/enigma2/python/Plugins/Extensions/Infopanel/'):
			imageType = 'openatv'
		elif path.exists('/usr/lib/enigma2/python/Blackhole'):
			imageType = 'blackhole'
		elif path.exists('/etc/init.d/start_pkt.sh'):
			imageType = 'pkt'
		else:
			imageType = 'unknown'
	if imgName.lower() == imageType.lower() :
		return True
	else:
		return False

def j00zekDEBUG(myText = ''):
	global append2file, myDEBUG
	if myDEBUG is None:
		return
	try:
		myFUNC = '%s(l%s)' % (inspect.stack()[1][3], inspect.stack()[1][2] )
		if append2file == False:
			append2file = True
			f = open(myDEBUG, 'w')
		else:
			f = open(myDEBUG, 'a')
		if myText[0:1] == '[':
			f.write('%s\n' % myText)
		else:
			f.write('[%s] %s\n' % ( myFUNC, myText ))
		f.close
	except Exception, e:
		system('echo "Exception:%s" >> %s' %( str(e), myDEBUG ))
	return
