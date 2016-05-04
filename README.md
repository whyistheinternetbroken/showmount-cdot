# showmount-cdot
This is the home of the showmount python plugin.

For questions, contact:

Justin Parisi - whyistheinternetbroken@gmail.com

or

Karthik Nagalingam - nkarthik@netapp.com
https://www.linkedin.com/in/karthikeyan-nagalingam-096b4454

This tool provides 7-Mode functionality in Clustered Data ONTAP for the "showmount -e" command as it is executed by an application as a workaround tool until the official ONTAP fix in 8.3.

It is a set of scripts which needs to be copied to the client machines on which the 'showmount -e' command will be executed and hence replacin the original showmount command binary.

This script is no longer officially supported by NetApp and is now released to the open source community. Enjoy!

###########################################################################################
###########################################################################################

The steps to use this showmout wrapper:

1. Move the existing /usr/sbin/showmount to /usr/sbin/showmount_old. This is very important step. The name *must* be showmount_old to ensure the plugin will fall back to the original showmount if not run against the specific cluster vserver.

2. Copy the files [NaServer.py, showmount.py, NaErrno.py, NaElement.py, showmount] from showmount_export folder to /usr/sbin.

3. Update the showmount file with proper username and password for the storage virtual machine access

4. Execute showmount -e <vserver data LIF>

Note: Please make sure the LIF "Role" is data and "Firewall policy" is mgmt, when you create the LIF from CLI or If you use system manager to create LIF (storage virtual machine -> select the svm -> configuration -> Network Interface -> create ) and make sure to select "Both" in "Role" screen of the LIF


