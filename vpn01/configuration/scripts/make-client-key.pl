#!/usr/bin/perl

use strict;

my $size = 16;
my $pass;
my $rsadir = "/usr/share/openvpn/easy-rsa/2.0/scripts";
my $tmpdir = "/tmp/openvpn_client";
my $pkitool = "${rsadir}/build-key";
my ($client, $user, $uid, $gid);
my ($file, @files);

if ($#ARGV != 0)
{
  die("Usage: make-client-key.pl <client>\n");
}

$client = $ARGV[0];
$ENV{'KEY_NAME'} = "$client";
$ENV{'KEY_CN'} = "$client";
print `$pkitool $client`;
if ($client =~ m/^([A-Za-z]*)-.*/)
{
  $user = $1;
}
else
{
  $user = $client;
}

# Setup the zipfile of relevant files
mkdir $tmpdir;
print `cp -a ${rsadir}/../keys/${client}.key ${tmpdir}/`;
print `cp -a ${rsadir}/../keys/${client}.crt ${tmpdir}/`;
print `cp -a ${rsadir}/../keys/ta.key ${tmpdir}/`;
print `cp -a ${rsadir}/../keys/ca.crt ${tmpdir}/`;
print `cp -a /root/configuration/client_tcp.conf ${tmpdir}/`;
print `cp -a /root/configuration/client_udp.conf ${tmpdir}/`;
$pass = random_string($size);
print `zip --password \'${pass}\' /root/${client}.zip ${tmpdir}/*`;
print "PW: $pass\n";
print `rm -rf ${tmpdir}`;

exit 0;


# SUBROUTINES

sub random_string {

  my $length = $_[0];
  my @chars = ('a'..'z','A'..'Z','0'..'9',"!","@","#","\$","%","^","&","*","(",")","_","-","=","+","{","}","[","]",";",":",",","<",".",">","/","?","\\","\`","\|","\~");
  my $result = "";
  my $i;

  for ($i = 0; $i < $length; $i++)
  {
    $result .= $chars[rand @chars];
  }

  return $result;
}

# EOF
