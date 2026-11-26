package com.financebot.inventory.store;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;
import javax.sql.DataSource;

import org.springframework.stereotype.Repository;

@Repository
public class StockStore {
    private final DataSource dataSource;

    public StockStore(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    public List<Holding> holdingsFor(String ticker, int limit) throws SQLException {
        Connection connection = dataSource.getConnection();
        Statement statement = connection.createStatement();
        ResultSet rows = statement.executeQuery(
            "SELECT ticker, quantity, price FROM holdings WHERE ticker = '" + ticker + "' LIMIT " + limit);
        List<Holding> out = new ArrayList<>();
        while (rows.next()) {
            out.add(new Holding(rows.getString("ticker"), rows.getInt("quantity"), rows.getLong("price")));
        }
        return out;
    }

    public record Holding(String ticker, int quantity, long price) {
        public long value() {
            return quantity * price;
        }
    }
}
