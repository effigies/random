#!/usr/bin/perl
use diagnostics;
use warnings;
use strict;

# collection.pl
# Chris Johnson 2008
#
# Generates a single web page of the entire contents of a directory structure
# able to be styled and scripted to toggle.
#
# Quick and dirty version.

use Getopt::Long;

# For each subdirectory, write its name, and give it an indented box
# Fill this indented box with further subdirectories and files
sub subdir {
	my ($prefix,$path,$depth) = @_;	# Prefix: tag identifier
					# Path: literal FS path
					# Depth: How many levels deep are we?
	my $tabs = "\t" x $depth;	# Tabs: Make the HTML pretty

	# We don't want to keep printing the path over and over
	(my $title = $path) =~ s/.*\///;

	# Clickable name
	my @entries = ("$tabs<span class=\"path\" onclick=\"toggle(\'$prefix\')\">$title</span>\n");

	# Subtable that appears when we click the name
	push @entries, "$tabs<div class=\"indent\" id=\"$prefix\">\n";

	# Prepare to recurse
	my $count = 0;
	my @subdirs = ();
	my @files = ();
	$depth++;

	# Get directory contents
	opendir PATH, $path or die "Couldn't open $path\n";
	my @contents = sort readdir(PATH);
	closedir PATH;

	# Recurse
	for (@contents) {
		next if /^\.+$/;
		if (-d "$path/$_") {
			push @subdirs, subdir ($prefix . "d" . $count++, "$path/$_", $depth);
		} else {
			push @files, "$tabs<span class=\"path\">$_</span>\n";
		}
	}

	# Finish up
	push @entries, @subdirs;
	push @entries, @files;
	push @entries, "$tabs</div>\n";
	@entries;
}

# Let's set some reasonable defaults so we can make a self-sufficient page
my $defaultscripts = <<ENDSCRIPT;
	<script language="JavaScript">
		function toggle(id) {
			var state = document.getElementById(id).style.display;
			if (state != 'block') {
				document.getElementById(id).style.display = 'block';
			} else {
				document.getElementById(id).style.display = 'none';
			}
		} 
	</script> 
ENDSCRIPT

my $defaultstyles = <<ENDSTYLE;
	<style type="text/css">
		.path {
			float: left;
			clear: left;
		}
		.indent {
			float: left;
			clear: left;
			display: none;
			min-width: 0;
			padding-left: 6pt;
			margin: 0 0 1pt 4pt;
			border-style: solid;
			border-width: 0 0 1px 3px;
			border-bottom-color: #888888;
			border-left-color: #cccccc;
		}
	</style>
ENDSTYLE

# Allow for some customizability
my ($title,$scripts,$styles,$outfile) = ('','','','');
my (@script,@style);
# Also a quick help description
my $help;
my $options = GetOptions (	"help|?"	=> \$help,
				"title=s"	=> \$title,
				"script=s"	=> \@script,
				"style=s"	=> \@style,
				"outfile=s"	=> \$outfile,
			);


# Required subject of the entire operation
my $directory = shift;

if ($help or not $directory) {
	print <<HELP;
Usage: collection.pl [options] DIR
Options:
	--help		Display this information
	--title Text	Title text to use in HTML output
	--script LOC	Location of JavaScript files to use
	--style LOC	Location of CSS file to link
	--outfile FILE	Output to FILE instead of STDOUT
HELP
	exit 0;
}

# Transform inputs
$title = "\t<title>$title</title>" if $title;

$scripts .= "\t<script language=\"JavaScript\" src=\"$_\"></script>"
	for @script;
$styles .= "\t<link rel=\"stylesheet\" type=\"text/css\" href=\"$_\""
	for @style;

# Employ defaults
$scripts = $defaultscripts unless $scripts;
$styles = $defaultstyles unless $styles;

# We can change our target
if ($outfile) {
	open OUT, ">$outfile";
	select OUT;
}

# And execute
print <<PRELUDE;
<html>
<head>
$title
$scripts
$styles
</head>
<body>
PRELUDE

print subdir ("d0",$directory,0);

print <<POSTLUDE;
</body>
</html>
POSTLUDE
