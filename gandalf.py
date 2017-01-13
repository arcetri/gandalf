#!/usr/bin/env python3

import os
import sys
import argparse
import logging

import yaml
import mako, mako.exceptions, mako.template
import tinydb


# Exception raised by parse_csv if input csv file
# has some logical errors (invalid ip/mac addresses etc)
class CsvIntegrityError(Exception): pass


class ViewSet:
    pass


def parse_csv(csvpath):
    return []


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
        logging.fatal("unable to open {}: {}".format(args.csvfile, exc.strerror))
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
            logging.fatal("unable to open {}: {}".format(args.var, exc.strerror))
            sys.exit(4)
        except yaml.error.YAMLError as exc:
            logging.fatal("yaml error: {}".format(exc))
            sys.exit(5)
    else:
        var = {}

    # Iterate over each input/output path pair
    for infile, outfile in find_templates(args.templates, args.output):

        # Create template
        try:
            template = mako.template.Template(filename=infile)
        except IOError as exc:
            logging.error("unable to open {}: {}".format(infile, exc.strerror))
            continue
        except mako.exceptions.MakoException as exc:
            logging.error("template error while reading {}: {}".format(infile, exc))
            continue

        # Render template
        try:
            output = template.render_unicode(var=var, db=db,
                                             host=tinydb.Query(), view=ViewSet)
        except Exception:
            tb = mako.exceptions.text_error_template().render().strip()
            logging.error("unhandled exception while rendering template {}:\n{}"
                          .format(infile, tb))
            continue

        # Make parent directories if does not exist
        dirname = os.path.dirname(outfile)
        if dirname:
            try:
                os.makedirs(dirname, exist_ok=True)
            except OSError as exc:
                logging.error("could not create directory {}: {}".format(dirname, exc.strerror))
                continue

        # Write rendered template
        try:
            with open(outfile, "w") as f:
                f.write(output)
        except IOError as exc:
            logging.error("could not write to file {}: {}".format(outfile, exc.strerror))
            continue


    # All done
    sys.exit(0)


if __name__ == "__main__":
    main()
