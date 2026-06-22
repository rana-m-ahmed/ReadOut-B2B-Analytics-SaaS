import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { expect, test, describe, vi } from 'vitest';
import { CsvUploader } from '../components/data/CsvUploader';
import { apiClient } from '../lib/api/client';

vi.mock('../lib/api/client', () => ({
  apiClient: {
    getUploadUrl: vi.fn(),
    profileDataset: vi.fn(),
  }
}));

describe('CsvUploader', () => {
  test('rejects oversized file client-side without API call', async () => {
    render(<CsvUploader onUploadComplete={() => {}} />);
    const input = screen.getByTestId('file-input') as HTMLInputElement;

    const bigFile = new File([''], 'huge.csv', { type: 'text/csv' });
    Object.defineProperty(bigFile, 'size', { value: 51 * 1024 * 1024 });

    fireEvent.change(input, { target: { files: [bigFile] } });

    await waitFor(() => {
      expect(screen.getByTestId('upload-error')).toBeInTheDocument();
      expect(screen.getByText(/File is too large/)).toBeInTheDocument();
      expect(apiClient.getUploadUrl).not.toHaveBeenCalled();
    });
  });

  test('successful upload flow calls API endpoints sequentially', async () => {
    const onUploadComplete = vi.fn();
    (apiClient.getUploadUrl as any).mockResolvedValue({ upload_url: 'http://fake', dataset_id: '123' });
    (apiClient.profileDataset as any).mockResolvedValue({});

    let loadCallback: any;
    const xhrMock = {
      open: vi.fn(),
      send: vi.fn(function(this: any) { 
        if (loadCallback) {
          this.status = 200;
          loadCallback();
        }
      }),
      upload: { addEventListener: vi.fn() },
      addEventListener: vi.fn((event, cb) => {
        if (event === 'load') loadCallback = cb;
      }),
      status: 200,
    };
    window.XMLHttpRequest = function() { return xhrMock; } as any;

    render(<CsvUploader onUploadComplete={onUploadComplete} />);
    const input = screen.getByTestId('file-input');

    const validFile = new File(['a,b\n1,2'], 'data.csv', { type: 'text/csv' });
    fireEvent.change(input, { target: { files: [validFile] } });

    const uploadBtn = await screen.findByTestId('upload-button');
    fireEvent.click(uploadBtn);

    await waitFor(() => {
      expect(apiClient.getUploadUrl).toHaveBeenCalledWith('data.csv', validFile.size);
      expect(xhrMock.open).toHaveBeenCalledWith('PUT', 'http://fake');
      expect(xhrMock.send).toHaveBeenCalled();
      expect(apiClient.profileDataset).toHaveBeenCalledWith('123');
      expect(onUploadComplete).toHaveBeenCalledWith('123');
    });
  });
});
