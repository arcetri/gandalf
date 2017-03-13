
# Gandalf

Gandalf is a command-line script that is designed to generate config files
from given templates. For DNS files Gandalf is also capable of tracking
version number and updating it only when something actually changed.

Gandalf is written in Python (version 3), it uses Mako as templating library
and TinyDB as an internal database that can be queried from templates.
The set of unit tests provided covers 100% of application code.


## 1. Installation

To install under global Python package path, use command

`./setup.py install`

This will install all necessary dependencies and create 'gandalf' shell command.


## 2. Usage

`./gandalf.py [-h] [-d DNSDIR] [-v VARFILE] csvfile templates output`

* _csvfile_ -- a CSV file that contains all the objects that you would like to
  participate in template rendering;
* _templates_ -- template file or directory of such files;
* _output_ -- a filesystem location where rendered templates are to be stored.
  If _templates_ is a file, then _output_ is interpreted as a file path.
  If _templates_ is a directory, then _output_ is considered to be directory.
  In later case after running Gandalf the file tree under _output_/ will mimic
  the file tree under _templates_/ (except the fact that '.mako' extension
  will be stripped from file names if present).
* _dnspath_ -- a path where the old DNS files are stored. It is used only to
  compare newly generated DNS files to the old ones to update version number
  only when necessary.
* _varfile_ -- a YAML file with come additional variables that can be accessed
  from templates.

For example, you can render a set of config files from example/ directory:

`./gandalf.py examples/network.csv examples/templates examples/rendered`

After that you can test the DNS file version update by calling

`./gandalf.py examples/network.csv examples/templates examples/rendered -d examples/rendered`

you will notice that if you haven't changed DNS files, then their version
numbers are preserved.


## 3. Input files

### 3.1. CSV file

The CSV file (that is the first argument to Gandalf) could have any columns
you would like it to have. However, some columns have special meaning and
special rules for value validation (although none of them is required to be present):

* _hostname_ -- DNS name of network entity. Needs to be non-empty string;
* _domain_ -- DNS domain. Needs to be non-empty string;
* _ip_ -- IP address. Should be a valid IP address;
* _vlan_ -- VLAN number. Should be in range (0, 4096);
* _type_ -- needs to be one of the following:
    * _head_ -- this entity corresponds head node main interface;
    * _comp_ -- corresponds to compute node main interface;
    * _alias_ -- corresponds to head/compute node secondary interface;
    * _cimc_ -- corresponds to CIMC.
* _resides_on_ -- hostname of other entity that this one is bound to.
  If _type_ is _alias_ -- means the main interface; if _type_ is _cimc_ -- means
  main interface of the node that this CIMC controls. No validation rules;
* _resides_on_type_ -- _type_ column value of the entity referred
  in _resides_on_ column. No validation rules;
* _cluster_ -- name of the cluster entity belongs to. No validation rules;
* _dev_ -- linux device name (e.g. _eno1_). No validation rules;
* _mac_ -- interface MAC address. Should be a valid MAC address (case-insensitive);

Note that CSV stands for "COMMA separated values". Therefore make sure that
your spreadsheet editor (such as Microsoft Excel) actually uses _commas_ to
delimit values rather than tabs or something else. If you get weird KeyError
exceptions during template rendering, this is issue is the first candidate.


### 3.2. Template files

The templating library used is Mako. You can read the full documentation of
all the capabilities provided by Mako on the official website of the library:
http://www.makotemplates.org/. However, a very little part of Mako functionality
is of most practical interest. Below is a quick summary.


#### 3.2.1. Basic templating functionality

When rendering template, Mako executes pieces of Python code that are embedded
into the template and pastes into the document whatever those Python
snippets evaluated into. The special syntax that is used for inline python code
is symbols ${ and }. For example, template file containing

```
3+4 is ${ 3+4 }
```

will be rendered into

```
3+4 is 7
```

since "3+4" is a valid Python expression that is getting evaluated. Notice
however that only one expression can be enclosed into ${ } construct, and
whatever this expression is evaluated into is pasted into the template.

You can also embed multiple Python expressions at once that are just executed
and empty string is pasted on their place. For example, this is useful for
importing modules or defining variables. This is done using <% %> construct.
Consider:

```
<%
    import datetime
    now = datetime.datetime.now()
%>
Current timestamp is ${ now.timestamp() }
```

will be rendered into something like

```

Current timestamp is 1488505803.32663
```

Notice that extra blank line was rendered instead of <% %> block. You can
prevent this by placing "Current timestamp" on the same line with "%>".

Comments can be added either within <% %> block after '#' symbol or in the
actual template body after '##' symbols. However, '##' works only at the
beginning of the line.


#### 3.2.2. Special template variables

There are some special variables defined in the template namespace that don't
have to do anything directly with Mako, but rather are Gandalf-specific.
Below is the list of such variables.

* _db_ -- TinyDB database instance that contains entities read from CSV file.
  Refer to point 3.2.3 of this Readme for functionality description;
* _host_ -- special symbol used to do queries on TinyDB (refer to point 3.2.3);
* _var_ -- a structure that contains whatever was read from _varfile_ YAML file;
* _view_ -- an object that contains functions for rendering CSV file objects
  into representations suitable for use in different config files. Reference
  to point 3.2.4 for documentation;
* _get_dns_version_ -- a function that returns a proper DNS zone file version
  (well, not really, but unless you dive into Gandalf implementation details
   you may think of it this way). Should be called on separate line (see examples);
* _FILE_NAME_ -- name of the current file being rendered.


#### 3.2.3. TinyDB database

The _db_ variable in the template namespace is a reference to TinyDB database
object. For a full API reference, see TinyDB website: https://tinydb.readthedocs.io
The basic usage is summarized below.

Get a list of all entities read from CSV file: `db.all()`
The resulting list consists of Python dictionaries. Every dictionary has
key-value pairs that correspond to CSV column values of some row. Row order
is arbitrary and not guaranteed to be preserved.

You can build conditional queries using a special symbol that is referenced
by _host_ variable. For example:
`db.search((host.vlan == 253) & (host.cluster != "montalcino")`
will return a list of rows that have column "vlan" equal to 253 and column
"cluster" not equal to "montalcino". You can construct any condition using
| for "or", & for "and", == and !=, "not" and some other predicates. Just make
sure to enclose your logical expressions into parenthesis.

There is also a way to query based on arbitrary boolean function. For example:
`db.search(host.vlan.test(lambda v: bool(v % 2)))`
will return the list of all rows that have an odd value in "vlan" column.


#### 3.2.4. View object

The _view_ variable contains an object that renders list of dictionaries
returned by TinyDB queries into string representation. There are multiple
representations available for different config files. A summary is given below.

* view.hosts -- returns a string suitable for use in /etc/hosts file;
* view.dns -- returns a string suitable for use in DNS zone files. There is a
  second positional argument named "type" that could be either "addr" (default)
  or "cname". In the first case, function returns hostname-to-ip matching; in
  latter case, it returns hostname-to-resides-on matching;
* view.rdns -- returns a string suitable for use in DNS zone files containing
  reverse DNS zone entries. It matches IP address to hostname and domain;
* view.dhcp -- returns a string suitable for use in DHCP config files. It has
  three optional parameters:
    * with_hostname -- bool, whether add option "host-name" or not;
    * router_ip -- if not None, then add option "routers" with given ip as a value;
    * filename -- if not None, then add option "filename" with given file path
      as a value.

There is also a convenience method view.setDefaultView. It is used as follows:

```
    view.setDefaultView(view.hosts)
    view(db.all) # will actually call view.hosts
```

To get a better understanding of how the tool works as a whole, see the examples
folder.
