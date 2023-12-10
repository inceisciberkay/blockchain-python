from block import Block

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

    @classmethod
    def create_from_list_of_block_dicts(cls, list_of_dicts):
        blocks = []
        for block_dict in list_of_dicts:
            block = Block.create_from_block_dict(block_dict)
            blocks.append(block)

        return Blockchain(blocks)
