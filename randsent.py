#!/usr/bin/env python3
"""
601.465/665 — Natural Language Processing
Assignment 1: Designing Context-Free Grammars
Assignment written by Jason Eisner
Modified by Kevin Duh
Re-modified by Alexandra DeLucia
Code template written by Alexandra DeLucia,
based on the submitted assignment with Keith Harrigian
and Carlos Aguirre Fall 2019
"""
#from curses import keyname
import os
import sys
import random
import argparse
from xml.dom.minidom import Element

# Want to know what command-line arguments a program allows?
# Commonly you can ask by passing it the --help option, like this:
#     python randsent.py --help
# This is possible for any program that processes its command-line
# arguments using the argparse module, as we do below.
#
# NOTE: When you use the Python argparse module, parse_args() is the
# traditional name for the function that you create to analyze the
# command line.  Parsing the command line is different from parsing a
# natural-language sentence.  It's easier.  But in both cases,
# "parsing" a string means identifying the elements of the string and
# the roles they play.

def parse_args():
    """
    Parse command-line arguments.
    Returns:
        args (an argparse.Namespace): Stores command-line attributes
    """
    # Initialize parser
    parser = argparse.ArgumentParser(description="Generate random sentences from a PCFG")
    # Grammar file (required argument)
    parser.add_argument(
        "-g",
        "--grammar",
        type=str, required=True,
        help="Path to grammar file",
    )
    # Start symbol of the grammar
    parser.add_argument(
        "-s",
        "--start_symbol",
        type=str,
        help="Start symbol of the grammar (default is ROOT)",
        default="ROOT",
    )
    # Number of sentences
    parser.add_argument(
        "-n",
        "--num_sentences",
        type=int,
        help="Number of sentences to generate (default is 1)",
        default=1,
    )
    # Max number of nonterminals to expand when generating a sentence
    parser.add_argument(
        "-M",
        "--max_expansions",
        type=int,
        help="Max number of nonterminals to expand when generating a sentence",
        default=450,
    )
    # Print the derivation tree for each generated sentence
    parser.add_argument(
        "-t",
        "--tree",
        action="store_true",
        help="Print the derivation tree for each generated sentence",
        default=False,
    )
    return parser.parse_args()


class Grammar:
    def __init__(self, grammar_file):
        """
        Context-Free Grammar (CFG) Sentence Generator
        Args:
            grammar_file (str): Path to a .gr grammar file
        
        Returns:
            self
        """
        # Parse the input grammar file
        self.rules = None
        self._load_rules_from_file(grammar_file)

    def _load_rules_from_file(self, grammar_file):
        """
        Read grammar file and store its rules in self.rules
        Args:
            grammar_file (str): Path to the raw grammar file 
        """

        # read all lines of grammar file
        with open(grammar_file, "r") as opened_file:
            file_str = opened_file.read()
            lines = file_str.split("\n")
        
        # remove problematic lines (empty, comments)
        rule_lines = []
        for line in lines:
            if len(line) != 0 and line[0] != '#':
                rule_lines.append(line)

        # remove trailing comments and extra whitespace
        for i in range(len(rule_lines)):
            try:
                new_end = rule_lines[i].index('#')
                rule_lines[i] = rule_lines[i][:new_end]
                rule_lines[i] = rule_lines[i].strip()
            except ValueError:
                rule_lines[i] = rule_lines[i].strip()

        # store rules in dictionary
        rule_map = {}
        for rule in rule_lines:
            rule_list = rule.split('\t')
            rule_value = []
            rule_value.append(rule_list[0])
            for word in rule_list[2].split(" "):
                rule_value.append(word)
            if rule_list[1] in rule_map:
                rule_map[rule_list[1]].append(rule_value)
            else:
                rule_map[rule_list[1]] = []
                rule_map[rule_list[1]].append(rule_value)

        # normalize rule probabilities
        rule_weights = {}
        for key in rule_map.keys():
            weight_sum = 0
            for rule in rule_map[key]:
                weight_sum += float(rule[0])
            rule_weights[key] = weight_sum
        
        # set boundaries for choice of a given rule when a number in [0, 1) is generated:
        #
        #   for 
        for key in rule_map:
            weight_sum = 0
            for rule in rule_map[key]:
                weight_sum += (float(rule[0]) / rule_weights[key])
                rule[0] = weight_sum

        # At this point:
        #       -> self.rules.keys()    contains LHSes (i.e. non-terminals)
        #       -> self.rules.values()  contains lists of all RHSes for each LHS
        #
        #       -> For a given element of a value specifying an RHS, val[i]:
        #               -> val[i][0]    contains relative probability thresholds
        #               -> val[i][1:]   contains all ordered RHS symbols as single elements
        self.rules = rule_map

        return

    def sample(self, derivation_tree, max_expansions, start_symbol):
        """
        Sample a random sentence from this grammar
        Args:
            derivation_tree (bool): if true, the returned string will represent 
                the tree (using bracket notation) that records how the sentence 
                was derived
                               
            max_expansions (int): max number of nonterminal expansions we allow
            start_symbol (str): start symbol to generate from
        Returns:
            str: the random sentence or its derivation tree
        """
        
        # initalize ordered list to track generated sentence
        sent = []
        sent.append(start_symbol)

        # modify list to fit tree format expectations
        if derivation_tree:
            sent.insert(0, "(")
            sent.append(")")

        # stop expanding when expansion limit is reached or there are no more symbols to expand
        num_expansions = 0
        while len(set(sent).intersection(set(self.rules.keys()))) != 0 and num_expansions < max_expansions:
            
            next_sym = sent[0]
            next_sym_index = 0

            # find the first unexpanded, expandable symbol in the sentence
            while (next_sym not in tuple(self.rules.keys())):
                next_sym = sent[next_sym_index]
                next_sym_index += 1
            
            # account for bracket placed if in tree mode
            if next_sym_index > 0:
                next_sym_index -= 1
            
            # generate a random decimal in [0, 1)
            random_fraction = random.uniform(0,1)
            for rule in self.rules[next_sym]:
                # since probabilties were normalized and boundaries set between [0, 1),
                # choose first rule for which random_fraction is less than boundary
                if random_fraction <= float(rule[0]):
                    random_rule = rule[1:]
                    break
            
            # add punctuation to help organize tree structure
            if derivation_tree:
                sent[next_sym_index] = sent[next_sym_index] + " ("

            # insert all members of RHS
            for i in range(len(random_rule)):
                sent.insert(next_sym_index + i + 1, random_rule[i])

            # if we wish to see how non-terminals were expanded (in tree mode),
            # leave them in, otherwise remove the first occurrence (i.e. the one 
            # we just expanded)
            if derivation_tree:
                sent.insert(next_sym_index + 1 + len(random_rule), ")") 
            else:
                sent.remove(next_sym)
            
            # only one expansion per loop
            num_expansions += 1

        # ellipsize unexpanded symbols
        for i in range(len(sent)):
            if sent[i] in self.rules.keys():
                sent[i] = "..."
        
        # format sentence to string
        out = " ".join(sent)

        return out


####################
### Main Program
####################
def main():
    # Parse command-line options
    args = parse_args()

    # Initialize Grammar object
    grammar = Grammar(args.grammar)

    # Generate sentences
    for i in range(args.num_sentences):
        # Use Grammar object to generate sentence
        sentence = grammar.sample(
            derivation_tree=args.tree,
            max_expansions=args.max_expansions,
            start_symbol=args.start_symbol
        )

        # Print the sentence with the specified format.
        # If it's a tree, we'll pipe the output through the prettyprint script.
        if args.tree:
            prettyprint_path = os.path.join(os.getcwd(), 'prettyprint')
            t = os.system(f"echo '{sentence}' | perl {prettyprint_path}")
        else:
            print(sentence)


if __name__ == "__main__":
    main()