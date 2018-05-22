import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from scipy.stats import zscore
from sklearn.metrics import adjusted_mutual_info_score
from natsort import natsorted
from matplotlib import rcParams

from .plot_utils import get_palettes, transform_basis



def get_nrows_and_ncols(num_figs, nrows, ncols):
	if nrows is None and ncols is None:
		nrows = int(np.sqrt(num_figs))
		ncols = (num_figs // nrows) + (num_figs % nrows > 0)
	elif nrows is None:
		nrows = (num_figs // ncols) + (num_figs % ncols > 0)
	elif ncols is None:
		ncols = (num_figs // nrows) + (num_figs % nrows > 0)

	return nrows, ncols

def set_up_kwargs(subplot_size, left, bottom, wspace, hspace):
	kwargs = {}
	if subplot_size is not None:
		kwargs['subplot_size'] = subplot_size
	if left is not None:
		kwargs['left'] = left
	if bottom is not None:
		kwargs['bottom'] = bottom
	if wspace is not None:
		kwargs['wspace'] = wspace
	if hspace is not None:
		kwargs['hspace'] = hspace

	return kwargs

def get_subplot_layouts(nrows = 1, ncols = 1, subplot_size = (4, 4), left = 0.2, bottom = 0.15, wspace = 0.4, hspace = 0.15, squeeze = True, sharex = True, sharey = True, frameon = False):
	left_margin = left * subplot_size[0]
	bottom_margin = bottom * subplot_size[1]
	right_space = wspace * subplot_size[0]
	top_space = hspace * subplot_size[1]

	figsize = (left_margin + subplot_size[0] * (1.0 + wspace) * ncols, bottom_margin + subplot_size[1] * (1.0 + hspace) * nrows)
	fig, axes = plt.subplots(nrows = nrows, ncols = ncols, figsize = figsize, squeeze = squeeze, sharex = sharex, sharey = sharey, frameon = frameon)

	fig.subplots_adjust(left = left_margin / figsize[0], bottom = bottom_margin / figsize[1], right = 1.0 - right_space / figsize[0], top = 1.0 - top_space / figsize[1], wspace = wspace, hspace = hspace)

	return fig, axes



def get_legend_ncol(label_size):
	return (1 if label_size <= 14 else (2 if label_size <= 30 else 3))

### Sample usage:
###    fig = plot_composition(data, 'louvain_labels', 'Individual', style = 'normalized', stacked = False)
def plot_composition(data, cluster, attr, style = 'frequency', stacked = True, logy = False, subplot_size = (6, 4), left = 0.15, bottom = None, wspace = 0.2, hspace = None):
	kwargs = set_up_kwargs(subplot_size, left, bottom, wspace, hspace)
	fig, ax = get_subplot_layouts(**kwargs)
	df = pd.crosstab(data.obs[cluster], data.obs[attr])
	df = df.reindex(index = natsorted(df.index.values), columns = natsorted(df.columns.values))

	if style == 'frequency':
		df = df.div(df.sum(axis = 1), axis = 0) * 100.0
	elif style == 'normalized':
		df = df.div(df.sum(axis = 0), axis = 1) * 100.0

	if logy and not stacked:
		df_sum = df.sum(axis = 1)
		df_new = df.cumsum(axis = 1)
		df_new = 10 ** df_new.div(df_sum, axis = 0).mul(np.log10(df_sum), axis = 0)
		df = df_new.diff(axis = 1).fillna(value = df_new.iloc[:, 0:1], axis = 1)
		df.plot(kind = 'bar', stacked = False, legend = False, logy = True, ylim = (1.01, df_sum.max() * 1.7), ax = ax)
	else:
		df.plot(kind = 'bar', stacked = stacked, legend = False, logy = logy, ax = ax)

	ax.grid(False)
	ax.set_xlabel('Cluster ID')
	ax.set_ylabel('Percentage' if style != 'count' else 'Count')
	ax.set_title("AMI = {0:.4f}".format(adjusted_mutual_info_score(data.obs[cluster], data.obs[attr])))
	ax.legend(loc = 'center left', bbox_to_anchor = (1.05, 0.5))

	return fig


### Sample usage:
###    fig = plot_scatter(data, 'tsne', ['louvain_labels', 'hdbscan_labels_soft'], nrows = 1, ncols = 2, alpha = 0.5)
def plot_scatter(data, basis, attrs, nrows = None, ncols = None, subplot_size = (4, 4), left = None, bottom = None, wspace = None, hspace = None, alpha = None, legend_fontsize = None):
	df = pd.DataFrame(data.obsm['X_' + basis][:, 0:2], columns = [basis + c for c in ['1', '2']])
	basis = transform_basis(basis)

	nattrs = len(attrs)
	nrows, ncols = get_nrows_and_ncols(nattrs, nrows, ncols)
	marker_size = 120000.0 / df.shape[0]

	kwargs = set_up_kwargs(subplot_size, left, bottom, wspace, hspace)
	fig, axes = get_subplot_layouts(nrows = nrows, ncols = ncols, squeeze = False, **kwargs)

	if legend_fontsize is None:
		legend_fontsize = rcParams['legend.fontsize']

	for i in range(nrows):
		for j in range(ncols):
			ax = axes[i, j]
			ax.grid(False)	
			ax.set_xticks([])
			ax.set_yticks([])

			if i * ncols + j < nattrs:
				attr = attrs[i * ncols + j]
				labels = data.obs[attr].astype('category')
				label_size = labels.cat.categories.size
				palettes = get_palettes(label_size)

				for k, cat in enumerate(labels.cat.categories):
					idx = np.isin(labels, cat)
					ax.scatter(df.iloc[idx, 0], df.iloc[idx, 1],
						   c = palettes[k],
						   s = marker_size,
						   marker = '.',
						   alpha = alpha,
						   edgecolors = 'none',
						   label = cat,
						   rasterized = True)
				ax.set_title(attr)
				legend = ax.legend(loc = 'center left', bbox_to_anchor = (1, 0.5), frameon = False, fontsize = legend_fontsize, ncol = get_legend_ncol(label_size))

				for handle in legend.legendHandles:
					handle.set_sizes([300.0])
			else:
				ax.set_frame_on(False)

			if i == nrows - 1:
				ax.set_xlabel(basis + '1')
			if j == 0 :
				ax.set_ylabel(basis + '2')

	return fig


### Sample usage:
###    fig = plot_scatter_groups(data, 'tsne', 'louvain_labels', 'Individual', nrows = 2, ncols = 4, alpha = 0.5)
def plot_scatter_groups(data, basis, cluster, group, nrows = None, ncols = None, subplot_size = (4, 4), left = None, bottom = None, wspace = None, hspace = None, alpha = None, legend_fontsize = None):
	df = pd.DataFrame(data.obsm['X_' + basis][:, 0:2], columns = [basis + c for c in ['1', '2']])
	basis = transform_basis(basis)

	marker_size = 120000.0 / df.shape[0]

	groups = data.obs[group].astype('category')
	ngroup = groups.cat.categories.size
	nrows, ncols = get_nrows_and_ncols(ngroup + 1, nrows, ncols)

	labels = data.obs[cluster].astype('category')
	label_size = labels.cat.categories.size
	palettes = get_palettes(label_size)
	legend_ncol = get_legend_ncol(label_size)

	kwargs = set_up_kwargs(subplot_size, left, bottom, wspace, hspace)
	fig, axes = get_subplot_layouts(nrows = nrows, ncols = ncols, squeeze = False, **kwargs)

	if legend_fontsize is None:
		legend_fontsize = rcParams['legend.fontsize']

	for i in range(nrows):
		for j in range(ncols):
			ax = axes[i, j]
			ax.grid(False)	
			ax.set_xticks([])
			ax.set_yticks([])

			gid = i * ncols + j
			if gid <= ngroup:
				if gid == 0:
					idx_g = np.ones(groups.shape[0], dtype = bool)
				else:
					idx_g = np.isin(groups, groups.cat.categories[gid - 1])
	
				for k, cat in enumerate(labels.cat.categories):
					idx = np.logical_and(idx_g, np.isin(labels, cat))
					ax.scatter(df.iloc[idx, 0], df.iloc[idx, 1],
						   c = palettes[k],
						   s = marker_size,
						   marker = '.',
						   alpha = alpha,
						   edgecolors = 'none',
						   label = cat,
						   rasterized = True)
				
				ax.set_title("All" if gid == 0 else str(groups.cat.categories[gid - 1]))
				legend = ax.legend(loc = 'center left', bbox_to_anchor = (1, 0.5), frameon = False, fontsize = legend_fontsize, ncol = legend_ncol)

				for handle in legend.legendHandles:
					handle.set_sizes([300.0])
			else:
				ax.set_frame_on(False)

			if i == nrows - 1:
				ax.set_xlabel(basis + '1')
			if j == 0 :
				ax.set_ylabel(basis + '2')

	return fig



### Sample usage:
###    fig = plot_scatter_genes(data, 'tsne', ['CD8A', 'CD4', 'CD3G', 'MS4A1', 'NCAM1', 'CD14', 'ITGAX', 'IL3RA', 'CD38', 'CD34', 'PPBP'])
def plot_scatter_genes(data, basis, genes, nrows = None, ncols = None, subplot_size = (4, 4), left = None, bottom = None, wspace = 0.3, hspace = None, alpha = None, use_raw = False):
	df = pd.DataFrame(data.obsm['X_' + basis][:, 0:2], columns = [basis + c for c in ['1', '2']])
	basis = transform_basis(basis)

	ngenes = len(genes)
	nrows, ncols = get_nrows_and_ncols(ngenes, nrows, ncols)
	marker_size = 120000.0 / df.shape[0]

	kwargs = set_up_kwargs(subplot_size, left, bottom, wspace, hspace)
	fig, axes = get_subplot_layouts(nrows = nrows, ncols = ncols, squeeze = False, **kwargs)

	X = data.raw[:, genes].X.toarray() if use_raw else data[:, genes].X.toarray()

	for i in range(nrows):
		for j in range(ncols):
			ax = axes[i, j]
			ax.grid(False)	
			ax.set_xticks([])
			ax.set_yticks([])

			if i * ncols + j < ngenes:
				gene_id = i * ncols + j
				img = ax.scatter(df.iloc[:, 0], df.iloc[:, 1],
					   s = marker_size,
					   c = X[:, gene_id],
					   # marker = '.',
					   alpha = alpha,
					   edgecolors = 'none',
					   cmap='viridis',
					   rasterized = True)

				left, bottom, width, height = ax.get_position().bounds
				rect = [left + width * (1.0 + 0.05), bottom, width * 0.1, height]
				ax_colorbar = fig.add_axes(rect)
				fig.colorbar(img, cax = ax_colorbar)

				ax.set_title(genes[gene_id])
			else:
				ax.set_frame_on(False)

			if i == nrows - 1:
				ax.set_xlabel(basis + '1')
			if j == 0 :
				ax.set_ylabel(basis + '2')

	return fig



### Sample usage:
###    fig = plot_scatter_gene_groups(data, 'tsne', 'CD8A', 'Individual', nrows = 3, ncols = 3)
def plot_scatter_gene_groups(data, basis, gene, group, nrows = None, ncols = None, subplot_size = (4, 4), left = None, bottom = None, wspace = 0.3, hspace = None, alpha = None, use_raw = False):
	df = pd.DataFrame(data.obsm['X_' + basis][:, 0:2], columns = [basis + c for c in ['1', '2']])
	basis = transform_basis(basis)

	marker_size = 120000.0 / df.shape[0]
	groups = data.obs[group].astype('category')
	ngroup = groups.cat.categories.size
	nrows, ncols = get_nrows_and_ncols(ngroup + 1, nrows, ncols)

	kwargs = set_up_kwargs(subplot_size, left, bottom, wspace, hspace)
	fig, axes = get_subplot_layouts(nrows = nrows, ncols = ncols, squeeze = False, **kwargs)

	X = data.raw[:, gene].X if use_raw else data[:, gene].X

	for i in range(nrows):
		for j in range(ncols):
			ax = axes[i, j]
			ax.grid(False)	
			ax.set_xticks([])
			ax.set_yticks([])

			gid = i * ncols + j
			if gid <= ngroup:
				if gid == 0:
					idx_g = np.ones(groups.shape[0], dtype = bool)
				else:
					idx_g = np.isin(groups, groups.cat.categories[gid - 1])

				img = ax.scatter(df.iloc[idx_g, 0], df.iloc[idx_g, 1],
					   s = marker_size,
					   c = X[idx_g],
					   # marker = '.',
					   alpha = alpha,
					   edgecolors = 'none',
					   cmap='viridis',
					   rasterized = True)

				left, bottom, width, height = ax.get_position().bounds
				rect = [left + width * (1.0 + 0.05), bottom, width * 0.1, height]
				ax_colorbar = fig.add_axes(rect)
				fig.colorbar(img, cax = ax_colorbar)

				ax.set_title("All" if gid == 0 else str(groups.cat.categories[gid - 1]))
			else:
				ax.set_frame_on(False)

			if i == nrows - 1:
				ax.set_xlabel(basis + '1')
			if j == 0 :
				ax.set_ylabel(basis + '2')

	return fig



### Sample usage:
###     cg = plot_heatmap(data, 'louvain_labels', ['CD8A', 'CD4', 'CD3G', 'MS4A1', 'NCAM1', 'CD14', 'ITGAX', 'IL3RA', 'CD38', 'CD34', 'PPBP'], use_raw = True, title="markers")
###     cg.savefig("heatmap.png", bbox_inches='tight', dpi=600)
def plot_heatmap(data, cluster, genes, use_raw = False, showzscore = False, title = "", **kwargs):
	sns.set(font_scale = 0.35)

	adata = data.raw if use_raw else data
	df = pd.DataFrame(adata[:, genes].X.toarray(), index = data.obs.index, columns = genes)
	if showzscore:
		df = df.apply(zscore, axis = 0)

	cluster_ids = data.obs[cluster].astype('category')
	idx = cluster_ids.argsort().values
	df = df.iloc[idx, :] # organize df by category order
	row_colors = np.zeros(df.shape[0], dtype = object) 
	palettes = get_palettes(cluster_ids.cat.categories.size)

	cluster_ids = cluster_ids[idx]
	for k, cat in enumerate(cluster_ids.cat.categories):
		row_colors[np.isin(cluster_ids, cat)] = palettes[k]

	cg = sns.clustermap(data = df,
				   cmap = 'RdBu_r',
				   row_colors = row_colors,
				   row_cluster = False,
				   col_cluster = True,
				   linewidths = 0,
				   yticklabels = [],
				   xticklabels = genes,
				   **kwargs)
	cg.ax_heatmap.set_ylabel('')
	# move the colorbar
	cg.ax_row_dendrogram.set_visible(False)
	dendro_box = cg.ax_row_dendrogram.get_position()
	dendro_box.x0 = (dendro_box.x0 + 2 * dendro_box.x1) / 3
	dendro_box.x1 = dendro_box.x0 + 0.02
	cg.cax.set_position(dendro_box)
	cg.cax.yaxis.set_ticks_position("left")
	cg.cax.tick_params(labelsize = 10)
	# draw a legend for the cluster groups
	cg.ax_col_dendrogram.clear()
	for k, cat in enumerate(cluster_ids.cat.categories):
		cg.ax_col_dendrogram.bar(0, 0, color = palettes[k], label = cat, linewidth = 0)
	cg.ax_col_dendrogram.legend(loc = "center", ncol = 15, fontsize = 10)
	cg.ax_col_dendrogram.grid(False)
	cg.ax_col_dendrogram.set_xticks([])
	cg.ax_col_dendrogram.set_yticks([])

	return cg
