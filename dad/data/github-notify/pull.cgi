#!/usr/bin/perl -w

use strict;
use warnings;

use CGI;
use JSON;

use LWP::Simple;

# open my $ofh, '>>', '/tmp/foo.txt';
my $json = JSON->new->utf8;
my $r = new CGI;

if ($r->request_method() eq 'GET') {
	print "Content-type: text/plain\n\nI'm awake!\n";
	exit 0;
}

my $json_text = $r->param('payload');
# print $ofh $json_text, "\n";
# close $ofh;

my $payload = $json->decode($json_text);
my $url = $payload->{'repository'}->{'url'};
if ($url =~ m%https://github.com/(ActiveState|Komodo|hpcloud)/(.*)$%) {
	exit 0 if not $2;
} elsif ($url =~ m%https://api.github.com/repos/(ActiveState|Komodo|hpcloud)/(.*)$%) {
	exit 0 if not $2;
}
my $oname = $1;
my $rname = $2;
$oname =~ s/[^a-zA-Z0-9_\-]//;
$rname =~ s/[^a-zA-Z0-9_\-]//;
my $output = `/usr/local/bin/update-repo.sh $oname $rname`;
# print $ofh $output;

# [103796] Ping jenkins projects that are assigned to this URL
# Only ping Jenkins if an actual change has gone through (rather than a tag or such).
#my $modified = 0;
#foreach my $c ($payload->{'commits'}) {
	## print $ofh %{$c}, "\n";
#
	#if (($c->{'added'} > 0) ||
	    #($c->{'removed'} > 0) ||
	    #($c->{'modified'} > 0)) {
		#$modified = 1;
	#} 
#}

#if ($modified) {
	my $jenkins_url = "http://hudson.activestate.com/hudson/git/notifyCommit?url=";
	my $new_jenkins_url = "http://jenkins.activestate.com/git/notifyCommit?url=";
	my $jenkins_dev_url = "http://dev-jenkins.activestate.com/git/notifyCommit?url=";
	my $gh_url = "https://github.com";
	$gh_url =~ s/$gh_url/http:\/\/git-mirrors.activestate.com\/github.com\/$oname\/$rname/g; 
	my $contents = get("${jenkins_url}${gh_url}");
	my $contents2 = get("${jenkins_dev_url}${gh_url}");
	my $contents3 = get("${new_jenkins_url}${gh_url}");
	# print $ofh $contents, "\n";
	# print $ofh $contents2, "\n";
	# print $ofh $contents3, "\n";
#}

# close $ofh;

print <<_EOF
Content-type: text/html

<html>
<head>
<title>Thank you!</title>
</head>
<body>
<p>I'll get to work on that.</p>
</body>
</html>
_EOF


