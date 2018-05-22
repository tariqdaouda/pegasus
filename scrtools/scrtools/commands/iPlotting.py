from .Base import Base
from ..plotting import make_interactive_plots

class iPlotting(Base):
	"""
Generate cluster composition plots.

Usage:
  scrtools iplot --attribute <attr> [options] <basis> <input_h5ad_file> <output_html_file>
  scrtools iplot -h

Arguments:
  basis                  Basis can be either 'tsne', 'fitsne', 'umap', 'diffmap', 'pca' or 'rpca'.
  input_h5ad_file        Single cell data with clustering done by Scanpy in h5ad file format.
  output_html_file       Output interactive htl plot file name.

Options:
  --attribute <attr>        Use attribute <attr> as labels in the plot.
  --is-real                 <attr> is real valued.
  --is-gene                 <attr> is a gene name.
  --log10                   If take log10 of real values.

  -h, --help             Print out help information.

Examples:
  scrtools iplot --attribute louvain_labels tsne Manton_BM.h5ad test.html
  scrtools iplot --attribute louvain_labels diffmap 
	"""
	def execute(self):
		kwargs = {
			'attr' : self.args['--attribute'],
			'isreal' : self.args['--is-real'],
      'isgene' : self.args['--is-gene'],
			'log10' : self.args['--log10']
		}

		make_interactive_plots(self.args['<input_h5ad_file>'], self.args['<basis>'], self.args['<output_html_file>'], **kwargs)
