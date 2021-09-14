import click
import dill
import os
from Transformer import Transformer

print("HERE")
print(os.getcwd())


@click.command()
@click.option("--in-path", default="/mnt/clean_text.data")
@click.option("--out-path", default="/mnt/tokenized_text.data")
def run_pipeline(in_path, out_path):
    spacy_transformer = Transformer()
    with open(in_path, "rb") as in_f:
        x = dill.load(in_f)
    y = spacy_transformer.predict(x)
    with open(out_path, "wb") as out_f:
        dill.dump(y, out_f)


if __name__ == "__main__":
    run_pipeline()
