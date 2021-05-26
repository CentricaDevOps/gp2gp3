.PHONY: install

install:
	poetry install
	poetry export -f requirements.txt -o requirements.txt
	rm -rf vendor
	poetry run python -m pip install -r requirements.txt -t vendor
	rm requirements.txt

croles:
	aws cloudformation create-stack --capabilities CAPABILITY_NAMED_IAM --stack-name sreGP23DirectorRoleCF --template-body file://cloudformation/gp23-director-role.yaml
	aws cloudformation create-stack --capabilities CAPABILITY_NAMED_IAM --stack-name sreGP23WorkerRoleCF --template-body file://cloudformation/gp23-worker-role.yaml

uroles:
	aws cloudformation update-stack --capabilities CAPABILITY_NAMED_IAM --stack-name sreGP23WorkerRoleCF --template-body file://cloudformation/gp23-worker-role.yaml
	aws cloudformation update-stack --capabilities CAPABILITY_NAMED_IAM --stack-name sreGP23DirectorRoleCF --template-body file://cloudformation/gp23-director-role.yaml

deploy:
	poetry run chalice deploy --stage=prod
