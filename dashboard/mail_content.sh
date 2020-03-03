#!/bin/bash
mail_id=()
subject=()
mail_report(){
	for i in $@ ; do
		if [ `echo $i|grep "@"` ]; then
			mail_id+=($i)
		else
			subject+=($i)
		fi
	done
	cat /root/log_analyzer_tool/dashboard/report/mail_report.html | mail -r "XYZ<XYZ@gmail.com>" -s "$(echo -e "${subject[@]}\nContent-Type: text/html")" "${mail_id[@]}"
}
mail_report $@
