#!/bin/bash
rm -fR site
mkdocs gh-deploy --clean
rm -fR site
