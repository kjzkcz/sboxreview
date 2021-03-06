{
    "cpu_partition": ["Interactive","BioCompute","Lewis","Serial","Dtn","hpc3","hpc4","hpc4rc","hpc5","hpc6","General","Gpu"],
    "gpu_partition": ["Gpu","gpu3","gpu4"],
    "interactive_partition_timelimit": {
	"Interactive": 4,
	"Dtn": 4,
	"Gpu": 2
    },
    "jupyter_partition_timelimit": {
	"Lewis": 8,
	"BioCompute": 8,
	"hpc4": 8,
	"hpc5": 8,
	"hpc6": 8,
	"Gpu": 2,
	"gpu3": 8,
	"gpu4": 8
    },
    "partition_qos": {
	"Interactive": "interactive",
	"Dtn": "dtn",
	"Serial": "seriallong",
	"gpu4": "gpu4"
    },
    "partition_general_account_deny": ["BioCompute","gpu3","gpu4","hpc6"],
    "disk_quota_paths": ["/home", "/data", "/gprs", "/storage/htc"]
}
