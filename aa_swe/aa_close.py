#!/usr/bin/env python3
from aa_swe.aa import aa_context

def main():
    with aa_context() as aa:
        aa.set_path(None)

if __name__ == "__main__":
    main()