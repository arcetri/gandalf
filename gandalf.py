#!/usr/bin/env python3

import os
import sys
import csv
import logging
import argparse
import itertools

import yaml
import tinydb
import mako, mako.exceptions, mako.template


# Exception raised by parse_csv if input csv file
# has some logical errors (missing columns, invalid ip/mac addresses etc)
class CsvIntegrityError(Exception): pass


class ViewSet:
    '''
        A class that contains static functions to render a list of hosts
        into some string representation.
    '''

    def setDefaultView(self, callable_):
        '''
            Set default callable to be called when __call__ is invoked.
            Parameters:
                callable_ - any callable object (meant to be ViewSet method,
                            but it is not strictly neccesary).
        '''
        self._default_view = callable_

    def __call__(self, *args, **kw):
        if hasattr(self, "_default_view"):
            return self._default_view(*args, **kw)
        raise ValueError("default view is not set, use setDefaultView()")

    @staticmethod
    def hosts(hosts):
        '''
            Render list of hosts into /etc/hosts format.
            For that first group host entries by ip address
            and then return string representation of every group.
            Parameters:
                hosts - list of host entities
            Return value:
                string suitable for use in /etc/hosts
        '''
        # Sort hosts by ip address
        hosts = sorted(hosts, key=lambda h: [int(x) for x in h["ip"].split(".")])

        # Render each group into hosts file entry
        lines = [] # list of strings
        for ip, host_group in itertools.groupby(hosts, key=lambda h: h["ip"]):
            all_names = [name for host in host_group for name in
                [host["hostname"], "{}.{}".format(host["hostname"], host["domain"])]]
            lines.append("{} {}".format(ip, " ".join(all_names)))

        # Render it all into one string
        return "\n".join(lines)

    @staticmethod
    def dns(hosts, type_="addr"):
        '''
            Render list of hosts into DNS zone file format.
            Two types of rendering are supported: 'addr' for direct IP address
            pointer and 'cname' for making a pointer to the entity that
            this entity resides on.
        '''
        if type_ == "addr":
            lines = ["{:<24}{:<8}{:<8}{}".format(h["hostname"], "IN", "A", h["ip"])
                    for h in hosts]
        elif type_ == "cname":
            lines = ["{:<24}{:<8}{:<8}{}".format(h["hostname"], "IN", "CNAME",
                    h["resides_on"]) for h in hosts]
        else:
            raise ValueError("Unknown DNS record type: {}".format(type_))
        return "\n".join(sorted(lines))


def parse_csv(csvpath):
    '''
        Parse given CSV file and return a list of dicts,
        where each dict represents a host on the network.
        Make all columns names lowercase and replace spaces with underscores.
        Check that the following columns exist: 'hostname', 'domain',
        'ip', 'mac', 'vlan'. Check IP/MAC addresses for validity.
        If column 'gendalf_ignore' is present, then any row
        that has non-blank value in this column is getting ignored.
        Parameters:
            csvpath - path to CSV file
        Return value:
            list of dicts, where each dict corresponds to CSV file row
        Raises:
            IOError if unable to open given file
            csv.Error if CSV file is invalid
            CsvIntegrityError if there are missing columns or invalid values
    '''

    # Define a function that transforms column names.
    # Make column name lowercase and replace spaces with underscores.
    colname_transform = lambda colname: colname.lower().replace(" ", "_").strip()

    # Define validator functions for every column.
    # Value considered invalid if validator returns False
    # or raises ValueError.
    column_validators = {
        "hostname": lambda s: bool(s),
        "domain": lambda s: bool(s),
        "vlan": lambda s: s.strip() == "" or 0 < int(s) < 4096,
        "ip": lambda s: s.count(".") == 3 and all(0 <= int(x) <= 255 and (x == "0" or x[0] != "0") for x in s.split(".")),
        "mac": lambda s: not s or s.count(":") == 5 and all(0 <= int(x,16) <= 255 and len(x) == 2 for x in s.split(":")),
        "entity_type": lambda s: s in ("comp", "head", "alias", "cimc", "fi", "hardware")
    }

    # Define column transformer functions.
    # Those functions are applied to corresponding columns
    # after value has been validated with functions above.
    # Note that by default all the values are stripped even before validating.
    column_transformers = {
        "vlan": lambda s: int(s) if s.strip() != "" else None,
    }

    # Go ahead and read csv file. This raises IOError and csv.Error
    with open(csvpath, "r") as f:
        raw_rows = tuple(csv.DictReader(f))

    # If file is empty - quit
    if not raw_rows:
        return []

    # Build the mapping of column names
    colname_map = {colname: colname_transform(colname) for colname in raw_rows[0].keys()}
    ignore_column = ([old_col for old_col, new_col in colname_map.items()
            if new_col == "gandalf_ignore"] + [None])[0] # column that says to ignore row

    # List of preprocessed rows
    rows = []

    # Do sanity checks and transforms
    for n, raw_row in enumerate(raw_rows, start=2):

        # If transformed columns contain non-blank 'gandalf_ignore' value,
        # then skip this row
        if raw_row.get(ignore_column, "").strip() != "":
            continue

        # Row after processing
        row = {}

        # For every column and value in row
        for colname, value in raw_row.items():

            # Transfrom column name and strip column value
            new_colname = colname_map[colname]
            value = value.strip()

            # Check is value is valid
            try:
                is_valid = column_validators.get(new_colname, lambda x: True)(value)
            except ValueError:
                is_valid = False
            if not is_valid:
                raise CsvIntegrityError("invalid value: {} (row {}, column '{}')"
                                        .format(repr(value), n, colname))

            # Update column name and value
            row[new_colname] = column_transformers.get(new_colname, lambda x: x)(value)

        # Append this row to the resulting list of rows
        rows.append(row)

    # Yay, seems ok
    return rows


def find_templates(inpath, outpath):
    '''
        Recursively find all template files in a given inpath
        and yield tuples of (template_path, output_path).
        Parameters:
            inpath - path to template file or directory with those files
            outpath - base path of output files.
        Returns:
            For each found template file yield a tuple of
            (template_path, output_path), where the first value
            is path to found template file, second value is
            a path to the output file for this template.
    '''
    if os.path.isfile(inpath):
        if not os.path.isdir(outpath):
            yield (inpath, outpath)
        else:
            outfile = os.path.join(outpath, os.path.basename(inpath))
            yield (inpath, outfile)
    else:
        for root, dirs, files in os.walk(inpath):
            for filename in files:
                template_path = os.path.join(root, filename)
                output_path = os.path.join(outpath, root[len(inpath):].strip("/"), filename)
                yield template_path, output_path


def main():

    # Define command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("csvfile", help="CSV file containing hosts")
    parser.add_argument("templates", help="template file or directory")
    parser.add_argument("output", help="output file or directory")
    parser.add_argument("-v", "--var", metavar="VARFILE",
                        help="yaml file with variables")

    # Parse arguments
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Parse CSV file
    try:
        hosts = parse_csv(args.csvfile)
    except IOError as exc:
        logging.fatal("unable to open '{}': {}".format(args.csvfile, exc.strerror))
        sys.exit(1)
    except csv.Error:
        logging.fatal("unable to parse csv file")
        sys.exit(2)
    except CsvIntegrityError as exc:
        logging.fatal("error in csv file: {}".format(exc))
        sys.exit(3)

    # Create in-memory database from the list of network entities
    db = tinydb.TinyDB(storage=tinydb.storages.MemoryStorage)
    db.insert_multiple(hosts)

    # Parse variables file (if given)
    if args.var:
        try:
            with open(args.var, "r") as f:
                var = yaml.read(f)
        except IOError as exc:
            logging.fatal("unable to open '{}': {}".format(args.var, exc.strerror))
            sys.exit(4)
        except yaml.error.YAMLError as exc:
            logging.fatal("yaml error: {}".format(exc))
            sys.exit(5)
    else:
        var = {}

    # Iterate over each input/output path pair
    for infile, outfile in find_templates(args.templates, args.output):

        # Strip '.mako' etension if present
        if outfile.endswith(".mako"):
            outfile = outfile[:-len(".mako")]

        # Create template
        try:
            template = mako.template.Template(filename=infile)
        except IOError as exc:
            logging.error("unable to open '{}': {}".format(infile, exc.strerror))
            continue
        except mako.exceptions.MakoException as exc:
            logging.error("template error while reading '{}': {}".format(infile, exc))
            continue

        # Render template
        try:
            output = template.render_unicode(var=var, db=db,
                                             host=tinydb.Query(), view=ViewSet())
        except Exception:
            tb = mako.exceptions.text_error_template().render().strip()
            logging.error("unhandled exception while rendering template '{}':\n{}"
                          .format(infile, tb))
            continue

        # Make parent directories if they do not exist
        dirname = os.path.dirname(outfile)
        if dirname:
            try:
                os.makedirs(dirname, exist_ok=True)
            except OSError as exc:
                logging.error("could not create directory '{}': {}".format(dirname, exc.strerror))
                continue

        # Write rendered template
        try:
            with open(outfile, "w", encoding="utf8") as f:
                f.write(output)
        except IOError as exc:
            logging.error("could not write to file '{}': {}".format(outfile, exc.strerror))
            continue


    # All done
    sys.exit(0)


if __name__ == "__main__":
    main()
