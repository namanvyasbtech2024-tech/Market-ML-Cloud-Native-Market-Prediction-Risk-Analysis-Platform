#!/usr/bin/env bash
# ==============================================================================
# Automated AWS S3 Static Website Deployment Script
# Deploys Market ML Frontend to AWS S3 with Static Website Hosting
# ==============================================================================
set -e

# Configuration
REGION="${AWS_REGION:-ap-south-1}"
BUCKET_NAME="${1:-market-ml-prediction-risk-platform}"

echo "=================================================="
echo "🚀 Deploying Market ML Frontend to AWS S3"
echo "Bucket Name: $BUCKET_NAME"
echo "AWS Region : $REGION"
echo "=================================================="

# 1. Create S3 Bucket
echo "Creating bucket s3://$BUCKET_NAME..."
if [ "$REGION" = "us-east-1" ]; then
    aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$REGION"
else
    aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$REGION" \
        --create-bucket-configuration LocationConstraint="$REGION"
fi

# 2. Disable Block Public Access
echo "Configuring public access permissions..."
aws s3api put-public-access-block --bucket "$BUCKET_NAME" --public-access-block-configuration \
    "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

# 3. Apply Public Read Bucket Policy
echo "Applying public read bucket policy..."
cat <<EOF > /tmp/s3_policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
    }
  ]
}
EOF
aws s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy file:///tmp/s3_policy.json
rm -f /tmp/s3_policy.json

# 4. Enable Static Website Hosting
echo "Enabling S3 Static Website Hosting..."
aws s3api put-bucket-website --bucket "$BUCKET_NAME" --website-configuration '{
  "IndexDocument": {"Suffix": "index.html"},
  "ErrorDocument": {"Key": "index.html"}
}'

# 5. Upload Website Assets
echo "Uploading frontend assets..."
aws s3 cp app/templates/index.html "s3://$BUCKET_NAME/index.html" --content-type "text/html"
aws s3 cp app/static/style_v3.css "s3://$BUCKET_NAME/static/style_v3.css" --content-type "text/css"
aws s3 cp app/static/style_v3.css "s3://$BUCKET_NAME/style_v3.css" --content-type "text/css"
aws s3 cp app/static/script_v52.js "s3://$BUCKET_NAME/static/script_v52.js" --content-type "application/javascript"
aws s3 cp app/static/script_v52.js "s3://$BUCKET_NAME/script_v52.js" --content-type "application/javascript"

echo ""
echo "=================================================="
echo "✅ DEPLOYMENT SUCCESSFUL!"
echo "=================================================="
echo "Project Deployment Link:"
echo "👉 http://$BUCKET_NAME.s3-website.$REGION.amazonaws.com"
echo "=================================================="
