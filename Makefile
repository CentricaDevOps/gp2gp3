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
	AWS_PROFILE=gfssap-payer aws organizations list-accounts |grep aws-GFSSAP-payer+CENNONPROD1 >/dev/null
	rm .chalice/config.json
	rm .chalice/deployed
	cd .chalice && ln -s sap-config.json config.json && ln -s sap-deployed deployed
	AWS_DEFAULT_REGION=eu-west-1 AWS_PROFILE=sap-payer poetry run chalice deploy --stage=prod


sapdelete:
	# test we have the correct profile enabled
	AWS_PROFILE=gfssap-payer aws organizations list-accounts |grep aws-GFSSAP-payer+CENNONPROD1 >/dev/null
	rm .chalice/config.json
	rm .chalice/deployed
	cd .chalice && ln -s sap-config.json config.json && ln -s sap-deployed deployed
	AWS_DEFAULT_REGION=eu-west-1 AWS_PROFILE=sap-payer poetry run chalice delete --stage=prod


cbilldeploy:
	# test we have the correct profile enabled
	AWS_PROFILE=centricabilling aws organizations list-accounts |grep  aws.CentricaBilling@centrica.com >/dev/null
	rm .chalice/config.json
	rm .chalice/deployed
	cd .chalice && ln -s cbill-config.json config.json && ln -s cbill-deployed deployed
	AWS_DEFAULT_REGION=eu-west-1 AWS_PROFILE=cbill-payer poetry run chalice deploy --stage=prod


cbilldelete:
	# test we have the correct profile enabled
	AWS_PROFILE=centricabilling aws organizations list-accounts |grep  aws.CentricaBilling@centrica.com >/dev/null
	rm .chalice/config.json
	rm .chalice/deployed
	cd .chalice && ln -s cbill-config.json config.json && ln -s cbill-deployed deployed
	AWS_DEFAULT_REGION=eu-west-1 AWS_PROFILE=cbill-payer poetry run chalice delete --stage=prod
