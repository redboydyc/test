import os, json
import sys, platform


py_version = sys.version.split(".")[0]
path = "/etc/squid/"
squid_conf = open("squid_conf").read()
JsonMenu = json.loads(open("menu.json").read())
	
	
def save_conf(file_path, conf):
	default = filter(lambda a: not a.startswith("#") and a.strip(), open(file_path).readlines())
	with open("default.conf", "w") as f:
		f.write("".join(default))
	with open(file_path, "w") as f:
		f.write(conf)
	

def installer(package, remove=False):
	installed = os.system("dpkg -l %s" % package)
	if remove:
		if not installed:
			os.system("sudo apt-get purge --auto-remove %s" % package)
	else:
		if installed:
			os.system("sudo apt-get update")
			os.system("sudo apt-get install %s -y" % package)


def restart(package):
	print("%s restart ediliyor bekleyin..." % package)
	os.system("sudo systemctl restart %s" % package)
	print("%s restart edildi" % (package))


def _input(key, port=True):
	while True:
		if py_version == "2":
			value = raw_input("%s Girin: " % key).strip()
		else:
			value = input("%s Girin: " % key).strip()
		
		if port:
			if not value.isdigit():
				print("Port sadece rakamlardan olusmalidir!")
				continue
			if int(value) > 65535:
				print("Port 65535 den buyuk olamaz!")
				continue
		else:
			if not value:
				print("%s girmelisiniz!" % key)
				continue
		return value
	

def squid(install=False, change_port=False, passwd=None):
	port = None
	if install:
		installer("squid")
		print("Su anki port 3128, giris yapmazsaniz bu gecerli olacaktir.")
		new = _input("Port")
		port = new if new else "3128"
			
	if change_port:
		conf = open(path + "squid.conf").read()
		current = conf.split("\nhttp_port ")[1].split("\n")[0]
		print("Su anki port %s, giris yapmazsaniz bu gecerli olacakir." % current)
		port = _input("Port")
		
	if port:
		save_conf(path + "squid.conf", squid_conf.format(port))
		restart("squid")
	
	if passwd == "set":
		installer("apache2-utils")
		os.system("sudo touch /etc/squid/squid_passwd")
		os.system("sudo chown proxy /etc/squid/squid_passwd")
		user = _input("User", port=False)
		os.system("sudo htpasswd /etc/squid/squid_passwd %s" % user)
		with open(path + "squid.conf") as f:
			config = f.read().replace("http_access allow all\n", 
				"auth_param basic program \
				/usr/lib/squid/basic_ncsa_auth \
				/etc/squid/squid_passwd\n\
				acl ncsa_users proxy_auth REQUIRED\n\
				http_access allow ncsa_users\n")
		with open(path + "squid.conf", "w") as f: 
			f.write(config)
		restart("squid")
		
	if passwd == "change":
		user = _input("User", port=False)
		os.system("sudo htpasswd /etc/squid/squid_passwd %s" % user)
		restart("squid")
		
	if passwd == "remove":
		os.remove("/etc/squid/squid_passwd")
		with open(path + "squid.conf") as f:
			config = f.read().replace("auth_param basic program \
				/usr/lib/squid/basic_ncsa_auth \
				/etc/squid/squid_passwd\n\
				acl ncsa_users proxy_auth REQUIRED\n\
				http_access allow ncsa_users\n",
				"http_access allow all\n")
		with open(path + "squid.conf", "w") as f: 
			f.write(config)
		restart("squid")
	print("Squid Kullanima Hazir.")
	

def dropbear(install=False):
	dropbear_path = "/etc/default/dropbear"
	if install:
		installer("dropbear")
		user = _input("User", port=False)
		os.system("adduser %s" % user)
		
	current_conf = open(dropbear_path).read()
	ssh_port = current_conf.split("DROPBEAR_PORT=")[1].split("\n")[0]
	print("Gecerli Dropbear Portu = " + ssh_port)
	port = _input("Yeni Port: ")
	new_conf = current_conf.replace(
		"DROPBEAR_PORT=%s\n" % ssh_port, 
		"DROPBEAR_PORT=%s\n" % port if port else ssh_port
	)
	new_conf = new_conf.replace("NO_START=1","NO_START=0")
	with open(dropbear_path, "w") as f:
		f.write(new_conf)
	restart("dropbear")
	print("DropBear Kullanima Hazir.")


if __name__ == "__main__":
		
	def menu_loop(menu):
		for i in range(1, len(menu)):
			indx = str(i)
			if not isinstance(menu, dict):
				exec(menu)
				os._exit(0)
			print(indx + "- " + list(menu[indx].keys())[0])
		print("0- Exit")
		sec = _input("Secim")
		if not menu.get(sec):
			print("Hatali secim, tekrar girin!")
			return menu
		key = list(menu[sec].keys())[0]
		if key == "Geri":
			return JsonMenu
		if key == "Exit":
			os._exit(0)
		return menu[sec][key]

	menu = JsonMenu
	while True:
		menu = menu_loop(menu)
	