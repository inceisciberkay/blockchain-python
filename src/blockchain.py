class Blockchain():
    difficulty = 5

    def __init__(self, blocks):
        self.blocks = blocks

    def to_list_of_dicts(self):
        # convert list of blocks to list of dictionaries
        blocks = []
        for block in self.blocks:
            blocks.append(block.to_dict())
            
        return blocks
