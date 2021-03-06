import re
from Bio import SeqIO
import numpy as np
import os
import h5py
import sys
from tqdm import tqdm
import logging

import click


def split_genome(genome="ATCGATATACCA", k=3):
    return re.findall("." * k, genome)


def genearte_genomes(genome="ATCGATATACCA", k=3, words=50):
    sentences = []
    for index in range(0, k):
        _genome = genome[index:]
        _sentence = split_genome(genome=_genome, k=k)
        _fraction = int(len(genome) / k) - len(_sentence)

        if _fraction > 0:
            _sentence.append("")

        sentences.append(np.array(_sentence, dtype="U"))

    return np.array(sentences)


def genome_to_doc(input_file="", kmer=16, f5=""):
    """ This function transforms a sequence genome to a document of kmers """

    records = []
    for record in SeqIO.parse(input_file, "fasta"):
        _genome = str(record.seq).upper()
        _kmer_count = int(len(_genome) / kmer)
        label = "__label__" + record.description.split('|')[1]
        records.append(
            {
                "sentences": genearte_genomes(genome=_genome, k=kmer),
                "id": record.id,
                "_kmer_count": _kmer_count,
                "label": label,
            }
        )

    return records


@click.command()
@click.option("--inputfile", required=True, help="input fasta file")
@click.option(
    "--outdir",
    default="",
    required=True,
    help="directory where the word2vec model was downloaded",
)
@click.option("--kmer", default=11, help="kmer length [default: 11]")
@click.option("--epoch", default=100, help="number of epochs [default: 100]")
@click.option("--dim", default=100, help="embedding dimension [default: 100]")
@click.option("--ws", default=5, help="window size [default: 5]")
@click.option("--thread", default=10, help="threads [default: 10]")
@click.option("--minn", default=4, help="minimum nmer [default: 4]")
@click.option("--maxn", default=5, help="maximum nmer [default: 5]")
@click.option("--lr", default=0.5, help="learning rate [default: 0.5]")
@click.option("--word_ngrams", default=1, help="word n grams [default: 1]")
@click.option("--mincount", default=5, help="minimum kmer count [default: 5]")
def train_word_vectors(
    inputfile,
    outdir,
    kmer,
    epoch,
    dim,
    ws,
    thread,
    mincount,
    minn,
    maxn,
    lr,
    word_ngrams,
):
    """
    train word vectors using fasttext.

    the input fasta file --inputfile is splitted into consecutive kmers
    of lenth --kmer. Thus, there are a total of --kmer versions of
    the same sequence.

    Once all "sentence" are generated, they are trained using the skipgram
    model from fasttext to generate a word vectors representation.

    """

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    log_file = logging.FileHandler(filename=outdir + "/wordvectors.log")
    log_stdout = logging.StreamHandler(sys.stdout)
    handlers = [log_file, log_stdout]

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s %(asctime)s - %(message)s",
        handlers=handlers,
    )

    log = logging.getLogger()

    log.info("getting sentences from " + inputfile + ": started")
    x = genome_to_doc(input_file=inputfile, kmer=kmer)
    log.info("getting sentences from " + inputfile + ": done")

    log.info("storing preprocesed file to outdir/sentences.tsv")
    fo = open(outdir + "/sentences.tsv", "w")

    for i in tqdm(x):
        for j in i["sentences"]:
            fo.write(" ".join(j) + " " + i['label'] + "\n")

    fasttext_cmd = (
        "fasttext supervised \
        -input "
        + outdir
        + "/sentences.tsv \
        -output "
        + outdir
        + "/model \
        -dim "
        + str(dim)
        + " \
        -ws "
        + str(ws)
        + " \
        -epoch "
        + str(epoch)
        + " \
        -thread "
        + str(thread)
        + " \
        -minCount "
        + str(mincount)
        + " \
        -minn "
        + str(minn)
        + " \
        -maxn "
        + str(maxn)
        + " \
        -lr "
        + str(lr)
        + " \
        -wordNgrams "
        + str(word_ngrams)
    )

    log.info(fasttext_cmd)
    os.system(fasttext_cmd)
    log.info("The process is done :)")

