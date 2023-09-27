FROM mindsgo-sz-docker.pkg.coding.net/neuroimage_analysis/base/msg_baseimage_cuda11:deepFS
MAINTAINER Chenfei <chenfei.ye@foxmail.com>


RUN pip install -i https://mirrors.aliyun.com/pypi/simple/ scikit-image \
	loguru \	
	argparse \
	dppd
	
	
RUN	apt-get clean && \
	rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* 

	
COPY ./ /
RUN chmod +x /volume2csv.py
CMD ["python", "/run.py"]