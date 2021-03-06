#!/usr/bin/python

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

output_directory = '/Users/lisapoole/Desktop'
cutoff_of_reads = '10'
asisi_cut_sites = '/Users/lisapoole/Sources/asisi_cut_sites.csv'
font = {'fontname':'Times New Roman'}
asisi_cut_sites = '/Users/temporary/genomes/Homo_sapiens_hg38/Homo_sapiens/UCSC/hg38/Sequence/AbundantSequences/asisi_cut_sites.csv'


# Indexing known AsiSI cut sites
known = pd.read_csv(asisi_cut_sites)
known['index_name'] = known['chr'].map(str) + '_' + known['start'].map(str) + '_' + known['end'].map(str)


def overlap_asisi_known(sample_base, save_name):
    #  This function will find peaks that overlap with known asisi cut sites
    # peak_file = '{}/peaks/{}_filtered_peaks.csv'.format(output_directory, sample_base)
    peak_file = '{}/peaks/{}_control_filtered.csv'.format(output_directory, sample_base, cutoff_of_reads)

    peaks = pd.read_csv(peak_file, comment='#')
    print('total number of filtered peaks', peaks.shape)

    peaks['index_name'] = peaks['chr'].map(str) + '_' + peaks['start'].map(str) + '_' + peaks['end'].map(str)
    overlaps = []
    for i in peaks['chr'].unique():
        known_index = known[known['chr'] == i]
        if len(known_index) == 0:
            continue
        known_ranges = list()
        for ind, row in known_index.iterrows():
            rng = set(range(row['start'], row['end']))
            known_ranges.append(rng)
        peak_index = peaks[peaks['chr'] == i]
        for ind, row in peak_index.iterrows():
            rng = set(range(row['start'], row['end']))
            for known_r in known_ranges:
                if len(known_r.intersection(rng)) > 0:
                    # print('Intersection', row['index_name'])
                    overlaps.append(row['index_name'])
    new_data = peaks[peaks['index_name'].isin(overlaps)]

    new_data.to_csv('{}/peaks/{}.csv'.format(output_directory, save_name), index=False)
    print('number of peaks at known sites', new_data.shape)


def peak_distance_to_known(sample_base):
#     calculate the distance from known asisi sites to peaks above threshold
    data_file = '{}/{}_control_filtered.csv'.format(output_directory, sample_base)
    peaks = pd.read_csv(data_file, comment='#')
    known = pd.read_csv(asisi_cut_sites, comment='#')
    distance = []
    start_end_of_closest = []
    # this iterates through each row
    for nmn, each in peaks.iterrows():
        chr_n = each['chr']
        # this just removed chr from naming
        chr_n = chr_n.replace('chr', '')
        # exclude all known sites that are not on this chr
        known_per_chr = known[known['chr']==chr_n]
        known_per_chr_array = np.array(known[known['chr']==chr_n])
        if len(known_per_chr) == 0:
            continue
        # now we want to compare to the start site
        # same as end site since they are only 8 long
        known_start = np.array(known_per_chr['start'])

        # we find all the start sites
        start_site = each['start']
        end_site = each['end']

        distances_start = np.abs(known_start - start_site)
        min_distance_start = np.min(distances_start)

        distances_end = np.abs(known_start - end_site)
        min_distance_end = np.min(distances_end)

        if min_distance_start < min_distance_end:
            index_of_where = np.where(distances_start==min_distance_start)[0]
            min_distance = min_distance_start
        else:
            index_of_where = np.where(distances_end == min_distance_end)[0]
            min_distance = min_distance_end

        chr_num, start, end = known_per_chr_array[index_of_where][0]
        location_of_closest = "{}_{}_{}".format(chr_num, start, end)
        distance.append(min_distance)
        start_end_of_closest.append(location_of_closest)
    peaks['distance_to_cut_site'] = distance
    peaks['closest_cut_site'] = start_end_of_closest
    print(np.min(peaks['distance_to_cut_site']))
    peaks.to_csv('{}/{}_with_cuts_distance_peaks.csv'.format(output_directory, sample_base), index=False)


def histogram_distance_from_known(sample_base):
#  This function creates a histogram of reads piled at peak summit
#     filename = '{}/peaks/{}_with_cuts_distance_peaks.csv'.format(output_directory, sample_base)
    filename = '{}/{}_with_cuts_distance_peaks.csv'.format(output_directory, sample_base)
    data = pd.read_csv(filename, comment='#', header=0)
    bins = range(0, 110000, 10000)
    data_for_hist = data.copy()
    cutoff = 100000
    data_for_hist.loc[data_for_hist['distance_to_cut_site'] > cutoff, 'distance_to_cut_site'] = cutoff + 1

    bins.append(cutoff + 10000)
    fig, ax = plt.subplots(figsize=(9, 5))
    fig.autofmt_xdate(rotation=90)
    plt.hist(data_for_hist['distance_to_cut_site'], bins=bins,
                       color='red')# rwidth=0.95)
    bin_labels = np.array(bins, dtype='|S4')
    bin_labels = []
    for i in bins:
        if i == 100000:
            bin_labels.append('>100000')
        elif i >100000:
            continue
        else:
            bin_labels.append('{}-{}'.format(i,i+10000))
    bins = np.array(bins)+5000
    ax.set_xticks(bins)
    ax.set_xticklabels(bin_labels, fontsize=10, ha='center')
    plt.xlim(0, 110000)
    plt.yscale('log', base=10)
    plt.title('Distance from known AsiSI cut sites', fontsize=20, **font)
    plt.ylabel('$log_{10}$(Frequency)', **font)
    # plt.ylabel('Frequency', **font)
    plt.xlabel('Distance to Cut Site', **font)
    for tick in ax.get_xticklabels():
        tick.set_fontname("Times New Roman")
    for tick in ax.get_yticklabels():
        tick.set_fontname("Times New Roman")
    plt.savefig("{}/{}_distance_to_known_plot.png".format(output_directory, sample_base), dpi=300, bbox_inches='tight')


def peak_known_distance_filtering(sample_base):
    # This removes peaks that are below the cutoff for number of reads determined to legitimate
    data_file = '{}/{}_with_cuts_distance_peaks.csv'.format(output_directory, sample_base)
    peaks = pd.read_csv(data_file, header=0)
    print('number of peaks', peaks.shape)
    new_peaks = peaks[peaks['distance_to_cut_site'] <=1000]
    print('number of peaks above cutoff', new_peaks.shape)
    new_peaks.to_csv('{}/{}_distance_1000.csv'.format(output_directory, sample_base), index=False)

# peak_distance_to_known('asisi')
histogram_distance_from_known('asisi')
# peak_known_distance_filtering('asisi')