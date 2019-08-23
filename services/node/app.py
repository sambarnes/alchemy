#!/usr/bin/env python3.7

import click

import main


HEADER = r"""
      o       
       o      
     ___      
     | |      
     | |      
     |o|             _      _                          
    .' '.       __ _| | ___| |__   ___ _ __ ___  _   _ 
   /  o  \     / _` | |/ __| '_ \ / _ \ '_ ` _ \| | | |
  :____o__:   | (_| | | (__| | | |  __/ | | | | | |_| |
  '._____.'    \__,_|_|\___|_| |_|\___|_| |_| |_|\__, |
                                                 |___/ 
"""


@click.command()
@click.option("--node-type", default="cloud", type=click.Choice(["local", "cloud"]))
@click.option("--testnet", is_flag=True)
def main(node_type, testnet):
    """Main entry point for the node"""
    print(HEADER)
    is_cloud = node_type == "cloud"
    main.run(testnet, is_cloud)


if __name__ == "__main__":
    main()
