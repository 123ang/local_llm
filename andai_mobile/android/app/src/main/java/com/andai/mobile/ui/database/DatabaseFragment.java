package com.andai.mobile.ui.database;

import android.graphics.Typeface;
import android.os.Bundle;
import android.text.TextUtils;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.HorizontalScrollView;
import android.widget.TableLayout;
import android.widget.TableRow;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.andai.mobile.R;
import com.andai.mobile.api.ApiClient;
import com.andai.mobile.databinding.FragmentDatabaseBinding;
import com.andai.mobile.databinding.ItemDatasetBinding;
import com.andai.mobile.models.DatasetItem;
import com.andai.mobile.utils.AuthManager;
import com.google.android.material.dialog.MaterialAlertDialogBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.google.gson.JsonSyntaxException;
import com.google.gson.reflect.TypeToken;

import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.List;
public class DatabaseFragment extends Fragment {

    private FragmentDatabaseBinding binding;
    private final com.google.gson.Gson gson = new com.google.gson.Gson();
    private final List<DatasetItem> items = new ArrayList<>();
    private DatasetAdapter adapter;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {
        binding = FragmentDatabaseBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        adapter = new DatasetAdapter();
        binding.rvDatasets.setLayoutManager(new LinearLayoutManager(requireContext()));
        binding.rvDatasets.setAdapter(adapter);
        loadDatasets();
    }

    private Integer requireCompanyId() {
        Integer id = AuthManager.getInstance(requireContext()).getCompanyId();
        if (id == null) {
            Toast.makeText(requireContext(), R.string.error_no_company, Toast.LENGTH_SHORT).show();
        }
        return id;
    }

    private void loadDatasets() {
        Integer companyId = requireCompanyId();
        if (companyId == null) return;

        binding.progress.setVisibility(View.VISIBLE);
        ApiClient.getInstance().getDatasets(companyId, new ApiClient.ApiCallback() {
            @Override
            public void onSuccess(String responseBody) {
                if (!isAdded()) return;
                binding.progress.setVisibility(View.GONE);
                try {
                    Type type = new TypeToken<List<DatasetItem>>() {
                    }.getType();
                    List<DatasetItem> list = gson.fromJson(responseBody, type);
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

    private void openRowsDialog(DatasetItem ds) {
        Integer companyId = requireCompanyId();
        if (companyId == null) return;

        binding.progress.setVisibility(View.VISIBLE);
        ApiClient.getInstance().getDatasetRows(companyId, ds.id, 100, 0, new ApiClient.ApiCallback() {
            @Override
            public void onSuccess(String responseBody) {
                if (!isAdded()) return;
                binding.progress.setVisibility(View.GONE);
                try {
                    JsonObject root = JsonParser.parseString(responseBody).getAsJsonObject();
                    JsonArray cols = root.getAsJsonArray("columns");
                    JsonArray rows = root.getAsJsonArray("rows");
                    int total = root.has("total") && !root.get("total").isJsonNull()
                            ? root.get("total").getAsInt()
                            : 0;

                    HorizontalScrollView hsv = new HorizontalScrollView(requireContext());
                    TableLayout table = new TableLayout(requireContext());
                    hsv.addView(table);

                    TableRow header = new TableRow(requireContext());
                    for (JsonElement c : cols) {
                        TextView tv = cell(c.getAsString(), true);
                        header.addView(tv);
                    }
                    table.addView(header);

                    if (rows != null) {
                        for (JsonElement rowEl : rows) {
                            JsonObject rowObj = rowEl.getAsJsonObject();
                            TableRow tr = new TableRow(requireContext());
                            for (JsonElement c : cols) {
                                String key = c.getAsString();
                                String val = "";
                                if (rowObj.has(key) && !rowObj.get(key).isJsonNull()) {
                                    JsonElement v = rowObj.get(key);
                                    val = cellValue(v);
                                }
                                tr.addView(cell(val, false));
                            }
                            table.addView(tr);
                        }
                    }

                    new MaterialAlertDialogBuilder(requireContext())
                            .setTitle(ds.displayName)
                            .setMessage(getString(R.string.rows_total_fmt, total))
                            .setView(hsv)
                            .setPositiveButton(android.R.string.ok, null)
                            .show();
                } catch (Exception e) {
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

    private TextView cell(String text, boolean header) {
        TextView tv = new TextView(requireContext());
        int pad = (int) (8 * getResources().getDisplayMetrics().density);
        tv.setPadding(pad, pad, pad, pad);
        tv.setText(text != null ? text : "");
        tv.setTextSize(header ? 12 : 11);
        if (header) {
            tv.setTypeface(null, Typeface.BOLD);
        }
        tv.setBackgroundResource(R.drawable.bg_chip_inactive);
        return tv;
    }

    private String cellValue(JsonElement v) {
        if (v.isJsonPrimitive()) {
            return v.getAsString();
        }
        return v.toString();
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }

    private class DatasetAdapter extends RecyclerView.Adapter<DsVH> {

        @NonNull
        @Override
        public DsVH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
            ItemDatasetBinding b = ItemDatasetBinding.inflate(getLayoutInflater(), parent, false);
            return new DsVH(b);
        }

        @Override
        public void onBindViewHolder(@NonNull DsVH holder, int position) {
            DatasetItem d = items.get(position);
            holder.b.tvName.setText(d.displayName);
            holder.b.tvDescription.setText(!TextUtils.isEmpty(d.description) ? d.description : "—");
            holder.b.tvCounts.setText(getString(R.string.rows_cols_label, d.rowCount, d.getColumnCount()));
            holder.itemView.setOnClickListener(v -> openRowsDialog(d));
        }

        @Override
        public int getItemCount() {
            return items.size();
        }
    }

    static class DsVH extends RecyclerView.ViewHolder {
        final ItemDatasetBinding b;

        DsVH(ItemDatasetBinding b) {
            super(b.getRoot());
            this.b = b;
        }
    }
}
