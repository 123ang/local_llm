package com.andai.mobile.ui.documents;

import android.net.Uri;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Toast;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.andai.mobile.R;
import com.andai.mobile.api.ApiClient;
import com.andai.mobile.databinding.FragmentDocumentsBinding;
import com.andai.mobile.databinding.ItemDocumentBinding;
import com.andai.mobile.models.DocumentItem;
import com.andai.mobile.utils.AuthManager;
import com.google.android.material.dialog.MaterialAlertDialogBuilder;
import com.google.gson.Gson;
import com.google.gson.JsonSyntaxException;
import com.google.gson.reflect.TypeToken;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.List;

public class DocumentsFragment extends Fragment {

    private FragmentDocumentsBinding binding;
    private final Gson gson = new Gson();
    private final List<DocumentItem> items = new ArrayList<>();
    private DocAdapter adapter;

    private final ActivityResultLauncher<String> pickPdf =
            registerForActivityResult(new ActivityResultContracts.GetContent(), this::onPdfUri);

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {
        binding = FragmentDocumentsBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        adapter = new DocAdapter();
        binding.rvDocuments.setLayoutManager(new LinearLayoutManager(requireContext()));
        binding.rvDocuments.setAdapter(adapter);

        binding.btnUpload.setOnClickListener(v -> pickPdf.launch("application/pdf"));
        loadDocuments();
    }

    private Integer requireCompanyId() {
        Integer id = AuthManager.getInstance(requireContext()).getCompanyId();
        if (id == null) {
            Toast.makeText(requireContext(), R.string.error_no_company, Toast.LENGTH_SHORT).show();
        }
        return id;
    }

    private void loadDocuments() {
        Integer companyId = requireCompanyId();
        if (companyId == null) return;

        binding.progress.setVisibility(View.VISIBLE);
        ApiClient.getInstance().getDocuments(companyId, new ApiClient.ApiCallback() {
            @Override
            public void onSuccess(String responseBody) {
                if (!isAdded()) return;
                binding.progress.setVisibility(View.GONE);
                try {
                    Type type = new TypeToken<List<DocumentItem>>() {
                    }.getType();
                    List<DocumentItem> list = gson.fromJson(responseBody, type);
                    items.clear();
                    if (list != null) {
                        items.addAll(list);
                    }
                    adapter.notifyDataSetChanged();
                    binding.layoutEmpty.setVisibility(items.isEmpty() ? View.VISIBLE : View.GONE);
                } catch (JsonSyntaxException e) {
                    Toast.makeText(requireContext(), R.string.error_parse, Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onError(String error) {
                if (!isAdded()) return;
                binding.progress.setVisibility(View.GONE);
                Toast.makeText(requireContext(), error, Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void onPdfUri(Uri uri) {
        if (uri == null) return;
        Integer companyId = requireCompanyId();
        if (companyId == null) return;

        String name = uri.getLastPathSegment();
        if (name == null) name = "upload.pdf";

        byte[] bytes;
        try {
            bytes = readAll(requireContext().getContentResolver().openInputStream(uri));
        } catch (IOException e) {
            Toast.makeText(requireContext(), R.string.error_read_file, Toast.LENGTH_SHORT).show();
            return;
        }

        binding.progress.setVisibility(View.VISIBLE);
        ApiClient.getInstance().uploadDocument(companyId, bytes, name, new ApiClient.ApiCallback() {
            @Override
            public void onSuccess(String responseBody) {
                if (!isAdded()) return;
                binding.progress.setVisibility(View.GONE);
                Toast.makeText(requireContext(), R.string.upload_ok, Toast.LENGTH_SHORT).show();
                loadDocuments();
            }

            @Override
            public void onError(String error) {
                if (!isAdded()) return;
                binding.progress.setVisibility(View.GONE);
                Toast.makeText(requireContext(), error, Toast.LENGTH_SHORT).show();
            }
        });
    }

    private static byte[] readAll(InputStream is) throws IOException {
        if (is == null) throw new IOException();
        ByteArrayOutputStream buf = new ByteArrayOutputStream();
        byte[] chunk = new byte[8192];
        int n;
        while ((n = is.read(chunk)) != -1) {
            buf.write(chunk, 0, n);
        }
        is.close();
        return buf.toByteArray();
    }

    private void confirmDelete(DocumentItem doc) {
        new MaterialAlertDialogBuilder(requireContext())
                .setTitle(R.string.confirm_delete)
                .setMessage(doc.originalName)
                .setPositiveButton(R.string.delete, (d, w) -> deleteDoc(doc))
                .setNegativeButton(R.string.cancel, null)
                .show();
    }

    private void deleteDoc(DocumentItem doc) {
        Integer companyId = requireCompanyId();
        if (companyId == null) return;
        binding.progress.setVisibility(View.VISIBLE);
        ApiClient.getInstance().deleteDocument(companyId, doc.id, new ApiClient.ApiCallback() {
            @Override
            public void onSuccess(String responseBody) {
                if (!isAdded()) return;
                binding.progress.setVisibility(View.GONE);
                loadDocuments();
            }

            @Override
            public void onError(String error) {
                if (!isAdded()) return;
                binding.progress.setVisibility(View.GONE);
                Toast.makeText(requireContext(), error, Toast.LENGTH_SHORT).show();
            }
        });
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }

    private class DocAdapter extends RecyclerView.Adapter<DocVH> {

        @NonNull
        @Override
        public DocVH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
            ItemDocumentBinding b = ItemDocumentBinding.inflate(getLayoutInflater(), parent, false);
            return new DocVH(b);
        }

        @Override
        public void onBindViewHolder(@NonNull DocVH holder, int position) {
            DocumentItem d = items.get(position);
            holder.b.tvFilename.setText(d.originalName != null ? d.originalName : d.filename);
            holder.b.tvStatus.setText(d.status != null ? d.status : "—");
            holder.b.tvChunks.setText(getString(R.string.chunks_label, d.chunkCount));
            holder.b.btnDelete.setOnClickListener(v -> confirmDelete(d));
        }

        @Override
        public int getItemCount() {
            return items.size();
        }
    }

    static class DocVH extends RecyclerView.ViewHolder {
        final ItemDocumentBinding b;

        DocVH(ItemDocumentBinding b) {
            super(b.getRoot());
            this.b = b;
        }
    }
}
