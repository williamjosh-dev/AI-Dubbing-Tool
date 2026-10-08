import { randomUUID } from 'node:crypto';
import { PutObjectCommand, S3Client } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';

const MAX_UPLOAD_BYTES = 100 * 1024 * 1024;
const ALLOWED_EXTENSIONS = new Set([
    'mp3', 'wav', 'ogg', 'flac', 'm4a', 'mp4', 'mov', 'avi', 'mkv', 'webm',
]);

function getR2Client() {
    const accountId = process.env.R2_ACCOUNT_ID;
    const accessKeyId = process.env.R2_ACCESS_KEY_ID;
    const secretAccessKey = process.env.R2_SECRET_ACCESS_KEY;

    if (!accountId || !accessKeyId || !secretAccessKey) {
        throw new Error('R2 storage is not configured.');
    }

    return new S3Client({
        region: 'auto',
        endpoint: `https://${accountId}.r2.cloudflarestorage.com`,
        credentials: { accessKeyId, secretAccessKey },
    });
}

export async function POST(request) {
    try {
        const payload = await request.json();
        const filename = typeof payload.filename === 'string' ? payload.filename : '';
        const contentType = typeof payload.contentType === 'string'
            ? payload.contentType
            : 'application/octet-stream';
        const size = Number(payload.size);
        const extension = filename.split('.').pop()?.toLowerCase();

        if (!filename || !extension || !ALLOWED_EXTENSIONS.has(extension)) {
            return Response.json({ detail: 'Unsupported file type.' }, { status: 400 });
        }
        if (!Number.isSafeInteger(size) || size <= 0 || size > MAX_UPLOAD_BYTES) {
            return Response.json(
                { detail: 'Files must be larger than 0 and no bigger than 100 MB.' },
                { status: 413 },
            );
        }

        const bucket = process.env.R2_BUCKET_NAME;
        if (!bucket) throw new Error('R2_BUCKET_NAME is not configured.');

        const objectKey = `uploads/${randomUUID()}.${extension}`;
        const command = new PutObjectCommand({
            Bucket: bucket,
            Key: objectKey,
            ContentType: contentType,
            ContentLength: size,
        });
        const uploadUrl = await getSignedUrl(getR2Client(), command, { expiresIn: 900 });

        return Response.json({ uploadUrl, objectKey, expiresIn: 900 });
    } catch (error) {
        console.error('Failed to create R2 upload URL:', error);
        return Response.json({ detail: 'Could not prepare the file upload.' }, { status: 500 });
    }
}
