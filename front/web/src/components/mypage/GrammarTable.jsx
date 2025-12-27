export default function GrammarTable({ data }) {
  return (
    <table className="table table-hover">
      <thead>
        <tr>
          <th>Grammar</th>
          <th>Function</th>
          <th>Meaning</th>
          <th>Boundary</th>
          <th>Count</th>
          <th>Recall</th>
        </tr>
      </thead>
      <tbody>
        {data.map((row, i) => (
          <tr key={i}>
            <td>{row.Grammar}</td>
            <td>{row.Function}</td>
            <td>{row.Meaning}</td>
            <td>{row.Boundary}</td>
            <td>{row.Count}</td>
            <td>{row.Recall}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
