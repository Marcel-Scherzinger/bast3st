from bast3st import Bast3StSpec, main

# you need one object of `Bast3StSpec`
spec = Bast3StSpec("Template specification")
# just as an example of possible operations
spec.set_block_count_limit(30, "You use too many blocks")

# run the following only, if the specification is used as a CLI
if __name__ == "__main__":
    # run the CLI, Bast3St includes specifically for specifications
    # and run it with the specification you just created
    main(spec)
