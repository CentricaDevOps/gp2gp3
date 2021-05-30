.PHONY: install

install:
	poetry install
	poetry export -f requirements.txt -o requirements.txt
	rm -rf vendor
	poetry run python -m pip install -r requirements.txt -t vendor
	rm requirements.txt

m2deploy:
	# test we have the correct profile enabled
	AWS_PROFILE=payer aws organizations list-accounts |grep dataplatform-bi >/dev/null
	rm .chalice/config.json
	rm .chalice/deployed
	cd .chalice && ln -s mode2-config.json config.json && ln -s mode2-deployed deployed
	AWS_DEFAULT_REGION=eu-west-1 AWS_PROFILE=payer poetry run chalice deploy --stage=prod


m2delete:
	# test we have the correct profile enabled
	AWS_PROFILE=payer aws organizations list-accounts |grep dataplatform-bi >/dev/null
	rm .chalice/config.json
	rm .chalice/deployed
	cd .chalice && ln -s mode2-config.json config.json && ln -s mode2-deployed deployed
	AWS_DEFAULT_REGION=eu-west-1 AWS_PROFILE=payer poetry run chalice delete --stage=prod

hivedeploy:
	# test we have the correct profile enabled
	AWS_PROFILE=awsbilling aws organizations list-accounts |grep honeycomb-prod >/dev/null
	rm .chalice/config.json
	rm .chalice/deployed
	cd .chalice && ln -s hive-config.json config.json && ln -s hive-deployed deployed
	AWS_DEFAULT_REGION=eu-west-1 AWS_PROFILE=awsbilling poetry run chalice deploy --stage=prod

hivedelete:
	AWS_PROFILE=awsbilling aws organizations list-accounts |grep honeycomb-prod >/dev/null
	rm .chalice/config.json
	rm .chalice/deployed
	cd .chalice && ln -s hive-config.json config.json && ln -s hive-deployed deployed
	AWS_DEFAULT_REGION=eu-west-1 AWS_PROFILE=awsbilling poetry run chalice delete --stage=prod

vodadeploy:
	# test we have the correct profile enabled
	AWS_PROFILE=vodafone-payer aws organizations list-accounts |grep aws-vodafone-payer+Prod-CC-GBS >/dev/null
	rm .chalice/config.json
	rm .chalice/deployed
	cd .chalice && ln -s voda-config.json config.json && ln -s voda-deployed deployed
	AWS_DEFAULT_REGION=eu-central-1 AWS_PROFILE=vodafone-payer poetry run chalice deploy --stage=prod


vodadelete:
	# test we have the correct profile enabled
	AWS_PROFILE=vodafone-payer aws organizations list-accounts |grep aws-vodafone-payer+Prod-CC-GBS >/dev/null
	rm .chalice/config.json
	rm .chalice/deployed
	cd .chalice && ln -s voda-config.json config.json && ln -s voda-deployed deployed
	AWS_DEFAULT_REGION=eu-central-1 AWS_PROFILE=vodafone-payer poetry run chalice delete --stage=prod


sapdeploy:
	# test we have the correct profile enabled
	AWS_PROFILE=sap-payer aws organizations list-accounts |grep aws-GFSSAP-payer+CENNONPROD1 >/dev/null
	rm .chalice/config.json
	rm .chalice/deployed
	cd .chalice && ln -s sap-config.json config.json && ln -s sap-deployed deployed
	AWS_DEFAULT_REGION=eu-west-1 AWS_PROFILE=sap-payer poetry run chalice deploy --stage=prod


sapdelete:
	# test we have the correct profile enabled
	AWS_PROFILE=sap-payer aws organizations list-accounts |grep aws-GFSSAP-payer+CENNONPROD1 >/dev/null
	rm .chalice/config.json
	rm .chalice/deployed
	cd .chalice && ln -s sap-config.json config.json && ln -s sap-deployed deployed
	AWS_DEFAULT_REGION=eu-west-1 AWS_PROFILE=sap-payer poetry run chalice delete --stage=prod

#croles:
#aws cloudformation create-stack --capabilities CAPABILITY_NAMED_IAM --stack-name sreGP23DirectorRoleCF --template-body file://cloudformation/gp23-director-role.yaml
#aws cloudformation create-stack --capabilities CAPABILITY_NAMED_IAM --stack-name sreGP23WorkerRoleCF --template-body file://cloudformation/gp23-worker-role.yaml
#
#uroles:
#aws cloudformation update-stack --capabilities CAPABILITY_NAMED_IAM --stack-name sreGP23WorkerRoleCF --template-body file://cloudformation/gp23-worker-role.yaml
#aws cloudformation update-stack --capabilities CAPABILITY_NAMED_IAM --stack-name sreGP23DirectorRoleCF --template-body file://cloudformation/gp23-director-role.yaml
